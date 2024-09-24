import telebot
from telebot import types
from menu import menu
import sqlite3

API_TOKEN = '7817351008:AAGKEjuJzEFM4WtvSgc8Hieopvkz108uijw'
bot = telebot.TeleBot(API_TOKEN)


connect = sqlite3.connect('users.db')
cur = connect.cursor()

# cur.execute('''
# CREATE TABLE IF NOT EXISTS Users (
# id INTEGER PRIMARY KEY,
# userid INTEGER NOT NULL,
# tg_username TEXT NOT NULL,
# username TEXT NOT NULL,
# org_adress TEXT NOT NULL,
# )
# ''')

connect.commit()


@bot.message_handler(commands=["start"])
def send_menu(message):
    pod_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    assorti_btn = types.KeyboardButton("/Ассортимент")
    zakaz_btn = types.KeyboardButton("/Заказать")
    pod_markup.add(assorti_btn, zakaz_btn)
    bot.send_message(
        message.chat.id,
        "Хош кушац? Заказывай \n (Кнопка Ассортимент)",
        reply_markup=pod_markup
        )


@bot.message_handler(commands=['Ассортимент'])
def assortiment(message):
    msg_markup = types.InlineKeyboardMarkup()
    plus_btn = types.InlineKeyboardButton(text="+", callback_data="plus")
    minus_btn = types.InlineKeyboardButton(text="-", callback_data="minus")
    msg_markup.add(minus_btn, plus_btn)

    for i in range(0, len(menu)):
        text = f"{menu[i]['name']}\n Цена {menu[i]['cost']}\n Кол-во: 0"
        photo = open(menu[i]["img"], 'rb')

        bot.send_photo(
            message.chat.id,
            photo, caption=text,
            reply_markup=msg_markup
            )


@bot.message_handler(commands=['Заказать'])
def zakaz(message):
    bot.send_message(
        message.chat.id,
        'Для заказа пожалуйста введите своё имя'
        )
    bot.register_next_step_handler(
         message,
         save_username
         )
    print(message.text)


def save_username(message):
    bot.send_message(
        message.chat.id,
        'Отлично. Теперь адрес'
        )
    print(message.text)
    bot.register_next_step_handler(message, save_adress)


def save_adress(message):
    bot.send_message(
        message.chat.id,
        'Хорошо.'
        )
    print(message.text)


@bot.callback_query_handler(func=lambda call: True)
def edit_ass(callback):
    text = callback.message.caption
    edit_text = text
    if callback.data == "plus" and int(text[-1]) >= 0:
        edit_text = text[:-1] + str(int(text[-1])+1)
    elif callback.data == "minus" and int(text[-1]) > 0:
        edit_text = text[:-1] + str(int(text[-1])-1)
    else:
        bot.answer_callback_query(
            callback_query_id=callback.id,
            text="Нельзя заказать меньше 0"
            )

    msg_text = edit_text
    id(callback.id)
    msg_markup = types.InlineKeyboardMarkup()
    plus_btn = types.InlineKeyboardButton(text="+", callback_data="plus")
    minus_btn = types.InlineKeyboardButton(text="-", callback_data="minus")
    msg_markup.add(minus_btn, plus_btn)

    print(callback.data)
    bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        caption=msg_text,
        reply_markup=msg_markup
        )


bot.infinity_polling()
