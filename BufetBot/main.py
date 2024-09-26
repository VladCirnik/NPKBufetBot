import telebot
from telebot import types
from menu import menu
import sqlite3

API_TOKEN = '7817351008:AAGKEjuJzEFM4WtvSgc8Hieopvkz108uijw'   # Replace with your actual token
bot = telebot.TeleBot(API_TOKEN)

con = sqlite3.connect('users.db', check_same_thread=False)
cur = con.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    username TEXT NOT NULL,
    org_adress TEXT NOT NULL
)
''')
con.commit()

@bot.message_handler(commands=["start"])
def send_menu(message):
    pod_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    assorti_btn = types.KeyboardButton("/Ассортимент")
    adress_btn = types.KeyboardButton("/Адрес Доставки")
    zakaz_btn = types.KeyboardButton("/Оформить заказ")
    pod_markup.add(assorti_btn, adress_btn)
    pod_markup.add(zakaz_btn)
    
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
        text = f"{menu[i]['name']}\nЦена: {menu[i]['cost']}\nКол-во: 0"
        with open(menu[i]["img"], 'rb') as photo:
            bot.send_photo(
                message.chat.id,
                photo,
                caption=text,
                reply_markup=msg_markup
            )

@bot.message_handler(commands=['Адрес Доставки'])
def adress(message):
    cur.execute('SELECT * FROM Users WHERE user_id=?', (message.from_user.id,))
    rows = cur.fetchall()

    if not rows:
        bot.send_message(
            message.chat.id,
            'Для заказа введите своё имя'
        )
        bot.register_next_step_handler(message, save_username)
    else:
        display_user_data(message, rows[0])

def save_username(message):
    global username
    username = message.text
    bot.send_message(message.chat.id, 'Теперь введите свой адрес:')
    bot.register_next_step_handler(message, save_adress)

def save_adress(message):
    global org_adress
    org_adress = message.text
    confirm_markup = types.InlineKeyboardMarkup()
    yes_btn = types.InlineKeyboardButton(text="Да", callback_data="save")
    change_btn = types.InlineKeyboardButton(text="Изменить", callback_data="edit")
    confirm_markup.add(yes_btn, change_btn)

    bot.send_message(
        message.chat.id,
        f'Подтвердите ваши данные:\nИмя: {username}\nАдрес: {org_adress}',
        reply_markup=confirm_markup
    )

@bot.callback_query_handler(func=lambda call: call.data in ["save", "edit"])
def handle_confirmation(callback):
    if callback.data == "save":
        cur.execute('INSERT OR REPLACE INTO Users (user_id, username, org_adress) VALUES (?, ?, ?)',
                    (callback.from_user.id, username, org_adress))
        con.commit()
        bot.send_message(callback.message.chat.id, "Ваши данные успешно сохранены.")
        bot.delete_message(callback.message.chat.id, callback.message.message_id)

    elif callback.data == "edit":
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, 'Введите новое имя:')
        bot.register_next_step_handler(callback.message, update_username)

def update_username(message):
    global username
    username = message.text
    bot.send_message(message.chat.id, 'Теперь введите новый адрес:')
    bot.register_next_step_handler(message, update_adress)

def update_adress(message):
    global org_adress
    org_adress = message.text
    cur.execute('UPDATE Users SET username=?, org_adress=? WHERE user_id=?',
                (username, org_adress, message.from_user.id))
    con.commit()
    bot.send_message(message.chat.id, "Ваши данные успешно обновлены.")

def display_user_data(message, user_data):
    msg_markup = types.InlineKeyboardMarkup()
    change_btn = types.InlineKeyboardButton(text="Изменить", callback_data="edit")
    msg_markup.add(change_btn)

    bot.send_message(
        message.chat.id,
        f'Ваши данные:\nИмя: {user_data[2]}\nАдрес: {user_data[3]}',
        reply_markup=msg_markup
    )
zakaz = []
@bot.callback_query_handler(func=lambda call: True)
def edit_ass(callback):
    tovar_name = callback.message.caption[:int(callback.message.caption.index("\n"))]
    text = callback.message.caption
    quantity = int(text.split(':')[-1].strip())
    if callback.data == "plus" and quantity >= 0:
        edit_text = text[:-1] + str(quantity + 1)
        if tovar_name not in zakaz:
            zakaz.append(tovar_name)
            for i in range(0, len(menu)):
                if menu[i]["name"] == tovar_name:
                    cost=menu[i]["cost"]
                    zakaz.append(cost)
                    print(zakaz)
        elif tovar_name in zakaz:
            
            for i in zakaz: # СДЕЛАТЬ НОРМАЛЬНОЕ ДОБАВЛЕНИЕ ТОВАРА В ЗАКАЗ
                if i == tovar_name:
                    
        print(tovar_name)
    if callback.data == "minus" and quantity > 0:
        edit_text = text[:-1] + str(quantity - 1)
    else:
        text
    
    if edit_text == text:
        bot.answer_callback_query(callback.id, text="Нельзя заказать меньше 0")
        return

    msg_markup = types.InlineKeyboardMarkup()
    plus_btn = types.InlineKeyboardButton(text="+", callback_data="plus")
    minus_btn = types.InlineKeyboardButton(text="-", callback_data="minus")
    msg_markup.add(minus_btn, plus_btn)

    bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        caption=edit_text,
        reply_markup=msg_markup
    )

bot.infinity_polling()
