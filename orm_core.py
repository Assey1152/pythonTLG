import os
import random

from dotenv import load_dotenv
import sqlalchemy
import json

from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from models import Base, Student, Word, Glossary, BaseGlossary

load_dotenv()
DSN = os.getenv('DSN')
engine = sqlalchemy.create_engine(DSN)
Session = sessionmaker(bind=engine)


def create_tables():
    Base.metadata.create_all(engine)


def clear_tables():
    Base.metadata.drop_all(engine)


def fill_glossary_db():
    with open("fixtures/base_glossary.json", encoding='utf-8') as f:
        json_data = json.load(f)
    with Session() as session:
        for row in json_data:
            session.add(Word(**row.get('fields')))
            session.add(BaseGlossary(word_id=row.get('pk')))
        session.commit()


def load_students():
    with Session() as session:
        students = session.query(Student.student_id).all()
        if students:
            return [s[0] for s in students]
        else:
            return []


def add_student(user_id):
    with Session() as session:
        st_id = session.query(Student.id).select_from(Student).filter(Student.student_id == user_id).first()
        if st_id is None:
            student = Student(student_id=user_id)
            session.add(student)
            session.commit()
            word_list = [r[0] for r in session.query(BaseGlossary.word_id).all()]
            for w in word_list:
                session.add(Glossary(student_id=student.id, word_id=w))
            session.commit()


def get_random_word(student_id, last_word_id=0):
    with Session() as session:
        query = session.query(Word.russian_word, Word.english_word).select_from(Glossary).join(Student).join(Word)
        word_list = query.filter(Student.student_id == student_id, Word.id != last_word_id).all()
        random.shuffle(word_list)
        if len(word_list) > 3:
            return word_list[0][0], word_list[0][1], [word_list[1][1], word_list[2][1], word_list[3][1]]
        else:
            match(len(word_list)):
                case 1:
                    lst = [word_list[0][1], word_list[0][1], word_list[0][1]]
                case 2:
                    lst = [word_list[0][1], word_list[1][1], word_list[1][1]]
                case 3:
                    lst = [word_list[0][1], word_list[1][1], word_list[2][1]]
            return word_list[0][0], word_list[0][1], lst


def delete_word_from_db(student_id, word):
    with Session() as session:
        word_id = session.query(Word.id).filter(Word.english_word.ilike(word)).first()[0]
        st_id = session.query(Student.id).filter(Student.student_id == student_id).first()[0]
        query = session.query(Glossary).filter(Glossary.student_id == st_id, Glossary.word_id == word_id)
        query = query.delete()
        session.commit()


def add_word_to_db(cid, russian_word, english_word):
    with Session() as session:
        word_id = session.query(Word.id).select_from(Word).filter(Word.russian_word.ilike(russian_word)).first()
        st_id = session.query(Student.id).filter(Student.student_id == cid).first()[0]
        if word_id is None:
            new_word = Word(russian_word=russian_word, english_word=english_word)
            session.add(new_word)
            session.commit()
            session.add(Glossary(student_id=st_id, word_id=new_word.id))
        else:
            session.add(Glossary(student_id=st_id, word_id=word_id[0]))
        session.commit()


def student_word_count(cid):
    with Session() as session:
        row_count = session.query(func.count()).select_from(Glossary).join(Student)
        return row_count.filter(Student.student_id == cid).scalar()
