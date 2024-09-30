import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from menu import menu
import sqlite3
import re

POVAR_CHAT_ID = -1002418156311
API_TOKEN = '7817351008:AAGKEjuJzEFM4WtvSgc8Hieopvkz108uijw'
bot = AsyncTeleBot(API_TOKEN)

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

user_orders = {}

@bot.message_handler(commands=["start"])
async def send_menu(message):
    pod_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    assorti_btn = types.KeyboardButton("/Ассортимент")
    adress_btn = types.KeyboardButton("/Адрес Доставки")
    zakaz_btn = types.KeyboardButton("/Оформить заказ")
    pod_markup.add(assorti_btn, adress_btn)
    pod_markup.add(zakaz_btn)

    await bot.send_message(
        message.chat.id,
        "Хош кушац? Заказывай \n (Кнопка Ассортимент)",
        reply_markup=pod_markup
    )
    print(message.chat.id)


@bot.message_handler(commands=['Ассортимент'])
async def assortiment(message):
    msg_markup = types.InlineKeyboardMarkup()
    plus_btn = types.InlineKeyboardButton(text="+", callback_data="plus")
    minus_btn = types.InlineKeyboardButton(text="-", callback_data="minus")
    msg_markup.add(minus_btn, plus_btn)

    for i in range(0, len(menu)):
        text = f"{menu[i]['name']}\nЦена: {menu[i]['cost']}\nКол-во: 0"
        with open(menu[i]["img"], 'rb') as photo:
            await bot.send_photo(
                message.chat.id,
                photo,
                caption=text,
                reply_markup=msg_markup
            )

@bot.message_handler(commands=['Адрес'])
async def adress(message):
    cur.execute('SELECT * FROM Users WHERE user_id=?', (message.from_user.id,))
    rows = cur.fetchall()

    if not rows:
        await bot.send_message(
            message.chat.id,
            'Для заказа введите своё имя'
        )
        await bot.register_next_step_handler(
            message,
            save_username
            )
    else:
        await display_user_data(message, rows[0])

async def save_username(message):
    global username
    username = message.text
    await bot.send_message(
        message.chat.id,
        'Теперь введите свой адрес:'
        )
    await bot.register_next_step_handler(
        message,
        save_adress
        )

async def save_adress(message):
    global org_adress
    org_adress = message.text
    confirm_markup = types.InlineKeyboardMarkup()
    yes_btn = types.InlineKeyboardButton(text="Да", callback_data="save")
    change_btn = types.InlineKeyboardButton(text="Изменить", callback_data="edit")
    confirm_markup.add(yes_btn, change_btn)

    await bot.send_message(
        message.chat.id,
        f'Подтвердите ваши данные:\nИмя: {username}\nАдрес: {org_adress}',
        reply_markup=confirm_markup
    )

@bot.callback_query_handler(func=lambda call: call.data in ["save", "edit"])
async def handle_confirmation(callback):
    if callback.data == "save":
        cur.execute('INSERT OR REPLACE INTO Users (user_id, username, org_adress) VALUES (?, ?, ?)',
                    (callback.from_user.id, username, org_adress))
        con.commit()
        await bot.send_message(
            callback.message.chat.id,
            "Ваши данные успешно сохранены."
            )
        await bot.delete_message(
            callback.message.chat.id,
            callback.message.message_id
            )

    elif callback.data == "edit":
        await bot.delete_message(
            callback.message.chat.id,
            callback.message.message_id
            )
        await bot.send_message(
            callback.message.chat.id,
            'Введите новое имя:'
            )
        await bot.register_next_step_handler(
            callback.message,
            update_username
            )

async def update_username(message):
    global username
    username = message.text
    await bot.send_message(
        message.chat.id,
        'Теперь введите новый адрес:'
        )
    await bot.register_next_step_handler(
        message,
        update_adress
        )

async def update_adress(message):
    global org_adress
    org_adress = message.text
    cur.execute('UPDATE Users SET username=?, org_adress=? WHERE user_id=?',
                (username, org_adress, message.from_user.id))
    con.commit()
    await bot.send_message(
        message.chat.id,
        "Ваши данные успешно обновлены."
        )

async def display_user_data(message, user_data):
    msg_markup = types.InlineKeyboardMarkup()
    change_btn = types.InlineKeyboardButton(text="Изменить", callback_data="edit")
    msg_markup.add(change_btn)

    await bot.send_message(
        message.chat.id,
        f'Ваши данные:\nИмя: {user_data[2]}\nАдрес: {user_data[3]}',
        reply_markup=msg_markup
    )

@bot.callback_query_handler(func=lambda call: True)
async def handle_callback(callback: types.CallbackQuery):
    zakaz = []
    if callback.data == "zakaz_done":
        cur.execute(f'SELECT * FROM Users WHERE user_id={callback.from_user.id}')
        rows = cur.fetchall()
        zakaz_to_chat = ""
        print(rows)
        zakaz_to_chat += f"Новый Заказ\n{await display_zakaz()}\n\nАдрес: {rows[0][3]}\nИмя: {rows[0][2]}"
        await bot.send_message(-1002418156311, zakaz_to_chat)
        del user_orders[callback.from_user.id]
        print(user_orders)
        
    elif callback.data in ["plus", "minus"]:
        tovar_name = callback.message.caption[:int(callback.message.caption.index("\n"))]
        text = callback.message.caption
        pattern = r'Кол-во:\s*(\d+)'
        match = re.search(pattern, text)
        for item in range(len(menu)):
            if menu[item]["name"] == tovar_name:
                cost = menu[item]["cost"]
        if match:
            quantity = int(match.group(1))

            if callback.data == "plus" and quantity >= 0:
                quantity += 1
                edit_text = f"{tovar_name}\nЦена: {cost}\nКол-во: {quantity}"
                if tovar_name not in zakaz:
                    zakaz.append(tovar_name)
                    zakaz.append(1)
                    for item in range(len(menu)):
                        if menu[item]["name"] == tovar_name:
                            zakaz.append(cost) 
                            break
                else:
                    for i in range(0, len(zakaz)):
                        if zakaz[i] == tovar_name:
                            zakaz[i + 1] += 1
                            break

                print(zakaz) 

            elif callback.data == "minus" and quantity > 0:
                quantity -= 1
                edit_text = f"{tovar_name}\nЦена: {cost}\nКол-во: {quantity}" 

                for i in range(len(zakaz)):
                    if zakaz[i] == tovar_name:
                        zakaz[i + 1] -= 1
                        if zakaz[i + 1] == 0:
                            del zakaz[i:i + 3]
                        break
        else:
            text
        
        if edit_text == text:
            await bot.answer_callback_query(
                callback.id,
                text="Нельзя заказать меньше 0"
                )
            return
        if callback.from_user.id not in user_orders:
            user_orders[callback.from_user.id] = zakaz
        elif callback.from_user.id in user_orders:
            for item in range(len(menu)):
                if menu[item]["name"] == tovar_name:
                    cost = menu[item]["cost"]
            if match:
                quantity = int(match.group(1))

                if callback.data == "plus" and quantity >= 0:
                    quantity += 1
                    edit_text = f"{tovar_name}\nЦена: {cost}\nКол-во: {quantity}"
                    if tovar_name not in user_orders[callback.from_user.id]:
                        user_orders[callback.from_user.id].append(tovar_name)
                        user_orders[callback.from_user.id].append(1)
                        for item in range(len(menu)):
                            if menu[item]["name"] == tovar_name:
                                user_orders[callback.from_user.id].append(cost) 
                                break
                    else:
                        for i in range(0, len(user_orders[callback.from_user.id])):
                            if user_orders[callback.from_user.id][i] == tovar_name:
                                user_orders[callback.from_user.id][i + 1] += 1
                                break
        print(user_orders)
        msg_markup = types.InlineKeyboardMarkup()
        plus_btn = types.InlineKeyboardButton(text="+", callback_data="plus")
        minus_btn = types.InlineKeyboardButton(text="-", callback_data="minus")
        msg_markup.add(minus_btn, plus_btn)

        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=edit_text,
            reply_markup=msg_markup
        )


@bot.message_handler(commands=["Оформить"])
async def get_zakaz(message):
    msg_markup = types.InlineKeyboardMarkup()
    zakaz_btn = types.InlineKeyboardButton(text="Все верно", callback_data="zakaz_done")
    msg_markup.add(zakaz_btn)
    if message.from_user.id in user_orders:
        await bot.send_message(
            message.chat.id,
            f"Ваш заказ \n\n{await display_zakaz(message.from_user.id)}",
            reply_markup=msg_markup
            )
    else:
        await bot.send_message(
            message.chat.id,
            "Вы должны заказать хоть что-то"
            )


async def display_zakaz(id):
    zakaz = user_orders[id]
    out = ""
    sum = 0
    for i in range(0, len(zakaz)):
        if type(zakaz[i]) == str:
            out += f"{zakaz[i+1]} - {zakaz[i]} \n"
            sum += zakaz[i+2] * zakaz[i+1]
    out += "Сумма: " + str(sum)

    return out


asyncio.run(bot.polling())
