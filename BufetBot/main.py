import telebot
from telebot import types
from menu import menu
import sqlite3

POVAR_CHAT_ID = -1002418156311
API_TOKEN = '7817351008:AAGKEjuJzEFM4WtvSgc8Hieopvkz108uijw'
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
    print(message.chat.id)

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

@bot.message_handler(commands=['Адрес'])
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
    if callback.data == "zakaz_done":
        cur.execute(f'SELECT * FROM Users WHERE user_id={callback.from_user.id}')
        rows = cur.fetchall()
        zakaz_to_chat = ""
        print(rows)
        zakaz_to_chat += f"Новый Заказ\n{display_zakaz()}\n\nАдрес: {rows[0][3]}\nИмя: {rows[0][2]}"
        bot.send_message(POVAR_CHAT_ID, zakaz_to_chat)

    elif callback.data in ["plus", "minus"]:
        tovar_name = callback.message.caption[:int(callback.message.caption.index("\n"))]
        text = callback.message.caption
        quantity = int(text.split(':')[-1].strip())
        if callback.data == "plus" and quantity >= 0:
            edit_text = text[:-1] + str(quantity + 1)
            if tovar_name not in zakaz:
                zakaz.append(tovar_name)
                zakaz.append(1)
                for i in range(0, len(menu)):
                    if menu[i]["name"] == tovar_name:
                        cost = menu[i]["cost"]
                        zakaz.append(cost)
            elif tovar_name in zakaz:
                for i in range(0, len(zakaz)):
                    if zakaz[i] == tovar_name:
                        zakaz[i+1] += 1
            print(zakaz)
        if callback.data == "minus" and quantity > 0:
            edit_text = text[:-1] + str(quantity - 1)
            for i in range(0, len(zakaz)):
                try:
                    if zakaz[i] == tovar_name:
                        zakaz[i+1] -= 1
                        if zakaz[i+1] == 0:
                            for j in range(0, 3):
                                del zakaz[i]
                except IndexError:
                    print("какой-то непонятный index error")
                    print(zakaz)
                print(zakaz)
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
    
        

@bot.message_handler(commands=["Оформить"])
def get_zakaz(message):
    msg_markup = types.InlineKeyboardMarkup()
    zakaz_btn = types.InlineKeyboardButton(text="Все верно", callback_data="zakaz_done")
    msg_markup.add(zakaz_btn)
    if zakaz != []:
        bot.send_message(message.chat.id, f"Ваш заказ \n\n{display_zakaz()}", reply_markup=msg_markup)
    else:
        bot.send_message(message.id, "Вы должны заказать хоть что-то")
def display_zakaz():
    out = ""
    sum = 0
    for i in range(0, len(zakaz)):
        if type(zakaz[i]) == str:
            out += f"{zakaz[i+1]} - {zakaz[i]} \n"
            sum += zakaz[i+2] * zakaz[i+1]
    out += "Сумма: " + str(sum)

    return out

# @bot.callback_query_handler(func=lambda call: True)
# def to_povar(callback):
    
bot.infinity_polling()
