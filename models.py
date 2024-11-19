import sqlalchemy as sq
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Student(Base):
    __tablename__ = "student"

    id = sq.Column(sq.Integer, primary_key=True)
    student_id = sq.Column(sq.BigInteger, unique=True)


class Word(Base):
    __tablename__ = "word"

    id = sq.Column(sq.Integer, primary_key=True)
    russian_word = sq.Column(sq.String(length=40), unique=True)
    english_word = sq.Column(sq.String(length=40), unique=True)


class Glossary(Base):
    __tablename__ = "glossary"

    id = sq.Column(sq.Integer, primary_key=True)
    student_id = sq.Column(sq.Integer, sq.ForeignKey("student.id"), nullable=False)
    word_id = sq.Column(sq.Integer, sq.ForeignKey("word.id"), nullable=False)

    student = relationship(Student, backref="glossary1")
    word = relationship(Word, backref="glossary2")


class BaseGlossary(Base):
    __tablename__ = "base_glossary"

    id = sq.Column(sq.Integer, primary_key=True)
    word_id = sq.Column(sq.Integer, sq.ForeignKey("word.id"), nullable=False)

    word = relationship(Word, backref="base_glossary")
