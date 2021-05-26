from datetime import datetime
import logging
import os
import re
import psycopg2
import configparser
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

DATABASE = os.getenv('POSTGRES_DB')
USER = os.getenv('POSTGRES_USER')
PASSWORD = os.getenv('POSTGRES_PASSWORD')
HOST = os.getenv("POSTGRES_DB_HOST")
PORT = "5432"


class NotFoundNote(Exception):
    def __init__(self, text):
        self.txt = text


def init_database():
    with psycopg2.connect(
            database=DATABASE,
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT) as con:
        cur = con.cursor()
        cur.execute(open("init.sql", "r").read())


def delete(user_id, id_for_user):
    with psycopg2.connect(
            database=DATABASE,
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT) as con:

        cur = con.cursor()
        cur.execute(f"SELECT id FROM note WHERE user_id = '{user_id}' AND id_for_user = '{id_for_user}'")
        if cur.fetchone() is None:
            raise NotFoundNote("Note not found")
        else:
            cur.execute(f"DELETE FROM note WHERE user_id = '{user_id}' AND id_for_user = '{id_for_user}'")


def get_note(user_id):
    notes = []  # str [id date text]
    with psycopg2.connect(
            database=DATABASE,
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT) as con:
        cur = con.cursor()
        cur.execute(f"SELECT id FROM users WHERE id = '{user_id}'")
        if cur.fetchone() is None:

            print("Пользователя нет в базе!")
        else:
            print("Такой пользователь уже есть ")
            cur.execute(f"SELECT * FROM note WHERE user_id = '{user_id}'")
            res = cur.fetchall()
            print(res)
            if res:
                notes.append('''
                    id    дата        запись 
                    ''')
            for e in res:
                date = datetime.strftime(e[4], '%d-%m-%Y')
                notes.append(f"{e[2]}    {date}   {e[3]}")

    return notes


def add_note(user_id, user_name, text, date):
    with psycopg2.connect(
            database=DATABASE,
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT) as con:
        cur = con.cursor()

        cur.execute(f"SELECT id FROM users WHERE id = '{user_id}'")
        if cur.fetchone() is None:
            cur.execute(f"INSERT INTO users (id,name) VALUES (%s,%s)", (user_id, user_name))
            print("Пользователь создан!")
        else:
            print("Такой пользователь уже есть ")
        cur.execute(f"SELECT id FROM note WHERE user_id = '{user_id}'")
        if cur.fetchone() is None:
            cur.execute("INSERT INTO note (user_id,id_for_user,text,date) VALUES (%s,%s,%s,%s)",
                        (user_id, 1, text, date))
        else:
            cur.execute(f"SELECT MAX(id_for_user) FROM note WHERE user_id = '{user_id}'")
            id_for_user = int(cur.fetchone()[0])

            cur.execute("INSERT INTO note (user_id,id_for_user,text,date) VALUES (%s,%s,%s,%s)",
                        (user_id, id_for_user + 1, text, date))


async def my_filter(message: types.Message):
    # do something here
    user_id = message.from_user.id
    text = message.text
    user_name = message.from_user.full_name
    print(user_id)
    print(text)
    print(user_name)

    return {'id': user_id, 'text': text, 'user_name': user_name}


async def add_filter(message: types.Message):
    s = re.split(r' ', message.text, maxsplit=2)

    dateString = s[1]
    try:
        dateFormatter = "%d.%m.%Y"
        date = datetime.strptime(dateString, dateFormatter)
    except ValueError:
        print("Неверная форма записи")
    note = s[2]
    return {"date": date, "note": note}


# @dp.message_handler(my_filter)
# async def my_message_handler(message: types.Message, id: int, text: str, user_name: str):
#     await message.reply(f'Ваш ид = {id}\nваше сообщение \n {text}\nВаше имя{user_name}')


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """

    await message.reply("Привет, я бот, который поможет тебе вести заметки !")


@dp.message_handler(commands=['help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("""
    Список команд: 
    /help - список команд
    /add date(d.m.Y) note - добавить заметку. День.Месяц.Год текст вашей заметки
    /get - получить список ваших заметок
    /delete id - удалить заметку по id
    """)


# @dp.message_handler(commands=['test'])
# async def send_welcome(message: types.Message):
#     print(message.from_user.full_name)
#     await message.reply("Test: ....")


@dp.message_handler(commands=['add'])
async def send_add_note(message: types.Message):
    s = re.split(r' ', message.text, maxsplit=2)

    try:
        dateString = s[1]
        dateFormatter = "%d.%m.%Y"
        date = datetime.strptime(dateString, dateFormatter)
        note = s[2]
        add_note(user_id=message.from_user.id, user_name=message.from_user.full_name, text=note, date=date)
        await message.reply(f"Добавлена запись\nДата: {date.day}.{date.month}.{date.year}\n"
                            f"Запись: {note} ")
    except ValueError:
        await message.reply(
            f"Неверная форма записи даты! \nЧтобы добавить заметку напишите /add дата(день.месяц.год) ваша_заметка ")
        print("Неверная форма записи")
    except IndexError:
        await message.reply(
            f"Неверная форма записи! \nЧтобы добавить заметку напишите /add дата(день.месяц.год) ваша_заметка ")
        print("Неверная форма записи")


@dp.message_handler(commands=['delete'])
async def send_add_note(message: types.Message):
    s = re.split(r' ', message.text, maxsplit=2)

    try:
        id_for_user = s[1]
        delete(user_id=message.from_user.id, id_for_user=id_for_user)
        await message.reply("Запись успешно удалена !")
    except NotFoundNote:
        await message.reply(f"Запись не найдена!")
        print("Запись не найдена")
    except IndexError:
        await message.reply(
            f"Неверная форма записи! \nЧтобы удалить заметку напишите /delete id")
        print("Неверная форма записи")


@dp.message_handler(commands=['get'])
async def send_get_note(message: types.Message):
    notes = get_note(message.from_user.id)
    if not notes:
        await message.reply(f"У вас нет не одной записи !\nДобавить их с помощью команды /add ")
    else:
        print(notes)
        await message.reply(f"Ваши записи: ")
        await message.reply("\n".join(notes))


if __name__ == '__main__':
    # logging.debug((u"START"))
    # logging.DEBUG((u"API TOKEN = ", API_TOKEN))
    # logging.DEBUG((u"DATABASE  =", DATABASE))
    # logging.DEBUG((u"USER  =", USER))
    # logging.DEBUG((u"PASSWORD  =", PASSWORD))
    # logging.DEBUG((u"HOST  =", HOST))
    init_database()
    executor.start_polling(dp, skip_updates=True)
