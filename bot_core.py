import os
import random
from dotenv import load_dotenv
from telebot import types
import telebot
from telebot.states import StatesGroup, State
import orm_core as orm


load_dotenv()
token = os.getenv('token')
known_users = []
user_step = {}
buttons = []
bot = telebot.TeleBot(token)


class Commands:
    ADD_WORD = 'Добавить слово'
    DELETE_WORD = 'Удалить слово'
    NEXT = 'Дальше'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    other_words = State()


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


def extend_menu_buttons(btns):
    next_btn = types.KeyboardButton(Commands.NEXT)
    add_word_btn = types.KeyboardButton(Commands.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Commands.DELETE_WORD)
    btns.extend([next_btn, add_word_btn, delete_word_btn])


@bot.message_handler(commands=['start', 'cards'])
def start_bot(message):
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        orm.add_student(cid)
        bot.send_message(cid, 'Добро пожаловать на уроки Английского языка!')
    else:
        bot.send_message(cid, 'Приветствую тебя снова на наших уроках!')
    create_cards(message)


def create_cards(message):
    cid = message.chat.id
    user_step[cid] = 0
    markup = types.ReplyKeyboardMarkup(row_width=2)
    global buttons
    buttons = []
    if orm.student_word_count(message.chat.id) == 0:
        hint = show_hint(f'К сожалению, в словаре не осталось больше слов.',
                         "Добавить новое слово?")
        add_word_btn = types.KeyboardButton(Commands.ADD_WORD)
        buttons = add_word_btn
        markup.add(*buttons)
        bot.send_message(message.chat.id, hint, reply_markup=markup)
    else:
        russian_word, target_word, other_words = orm.get_random_word(cid)
        target_word_btn = types.KeyboardButton(target_word)
        other_words_btns = [types.KeyboardButton(word) for word in other_words]
        buttons = [target_word_btn] + other_words_btns
        random.shuffle(buttons)
        extend_menu_buttons(buttons)
        markup.add(*buttons)
        hint = f'Выбери перевод слова: {russian_word}'
        bot.send_message(message.chat.id, hint, reply_markup=markup)

        bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = target_word
            data['translate_word'] = russian_word
            data['other_words'] = other_words


@bot.message_handler(func=lambda message: message.text == Commands.NEXT)
def next_word(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Commands.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    user_step[cid] = 1
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    global buttons
    buttons = []
    next_btn = types.KeyboardButton(Commands.NEXT)
    add_word_btn = types.KeyboardButton(Commands.ADD_WORD)
    buttons.extend([next_btn, add_word_btn])
    markup.add(*buttons)
    hint = 'Введите добавляемое слово:'
    bot.send_message(message.chat.id, hint, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == Commands.DELETE_WORD)
def delete_word(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        orm.delete_word_from_db(message.chat.id, data['target_word'])
        word_count = orm.student_word_count(message.chat.id)
        hint = show_hint(f"Слово {data['translate_word']} удалено из словаря",
                         f"В словаре осталось: {word_count} слов")
        buttons.clear()
        next_btn = types.KeyboardButton(Commands.NEXT)
        add_word_btn = types.KeyboardButton(Commands.ADD_WORD)
        buttons.extend([next_btn, add_word_btn])
        markup.add(*buttons)
        bot.send_message(message.chat.id, hint, reply_markup=markup)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    cid = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    match (user_step[cid]):
        case 0:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                target_word = data['target_word']
                if text == target_word:
                    hint_text = ["Правильно!", show_target(data)]
                    hint = show_hint(*hint_text)
                    buttons.clear()
                    extend_menu_buttons(buttons)
                else:
                    for btn in buttons:
                        if btn.text == text:
                            btn.text = text + '❌'
                            break
                    hint = show_hint('Ошибочка вышла!',
                                     f"Попробуй еще раз вспомнить перевод слова {data['translate_word']}")
        case 1:
            user_step[cid] = 2
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['translate_word'] = text
                hint = show_hint('Введите перевод добавляемого слова:',
                                 f"{text} -> ?")
        case 2:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                russian_word = data['translate_word']
                orm.add_word_to_db(cid, russian_word, text)
                word_count = orm.student_word_count(cid)
                hint = show_hint('Добавлено новое слово:',
                                 f"{text} -> {data['translate_word']}",
                                 f"Количество изучаемых слов: {word_count}")
                user_step[cid] = 0
                buttons.clear()
                extend_menu_buttons(buttons)
        case _:
            hint = 'Что-то пошло не так.'

    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


def bot_init():
    orm.clear_tables()
    orm.create_tables()
    orm.fill_glossary_db()
    orm.add_student(536)
    known_users.extend(orm.load_students())
    bot.polling()

