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

user_states = {}
user_orders = {}


                        # Приветствие и добавление всех кнопок в клаву
@bot.message_handler(commands=["start"])
async def send_menu(message): 
    keyboard_buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
    assortment_button = types.KeyboardButton("/Ассортимент")
    adress_button = types.KeyboardButton("/Адрес Доставки")
    order_button = types.KeyboardButton("/Оформить заказ")
    keyboard_buttons.add(assortment_button, adress_button)
    keyboard_buttons.add(order_button)

    await bot.send_message(
        message.chat.id,
        "Хош кушац? Заказывай \n (Кнопка Ассортимент)",
        reply_markup=keyboard_buttons
    )
    print(message.chat.id)

@bot.message_handler(commands=['Ассортимент'])
async def assortiment(message):  # отправление всего меню из menu.py
    message_markup_assortment = types.InlineKeyboardMarkup() # кнопки В СООБЩЕНИЕ минус/плюс для кол-ва позиции 
    plus_button = types.InlineKeyboardButton(text="+", callback_data="plus")
    minus_button = types.InlineKeyboardButton(text="-", callback_data="minus")
    message_markup_assortment.add(minus_button, plus_button)

    for i in range(0, len(menu)): # формирование меню
        Menu_assortment = f"{menu[i]['name']}\nЦена: {menu[i]['cost']}\nКол-во: 0"
        with open(menu[i]["img"], 'rb') as photo:
            await bot.send_photo(
                message.chat.id,
                photo,
                caption=Menu_assortment,
                reply_markup=message_markup_assortment
            )
@bot.message_handler(commands=['Адрес'])
async def adress(message): # выводит адрес доставки по кнопке
    cur.execute('SELECT * FROM Users WHERE user_id=?', (message.from_user.id,))
    rows = cur.fetchall()

    if not rows: # если user_id нет в бд, то он добавляет
        await bot.send_message(
            message.chat.id,
            'Для заказа введите своё имя:'
        )
        user_states[message.from_user.id] = 'waiting_for_name'
    else:
        await display_user_data(message, rows[0])  # если user_id есть то выводит имеющийся адрес

                        # ------------------------- сохранение Адреса и Имени в бд --------------------------
@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == 'waiting_for_name')
async def save_username(message):  # сохранение имени заказчика в бд
    global username
    username = message.text
    user_states[message.from_user.id] = 'waiting_for_address'
    await bot.send_message(
        message.chat.id,
        'Теперь введите свой адрес:'
    )

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == 'waiting_for_address')
async def save_address(message): # сохранение адреса заказчика в бд
    global org_adress
    org_adress = message.text
    confirm_markup = types.InlineKeyboardMarkup()
    yes_btn = types.InlineKeyboardButton(text="Да", callback_data="save")
    confirm_markup.add(yes_btn)

    await bot.send_message(
        message.chat.id,
        f'Подтвердите ваши данные:\nИмя: {username}\nАдрес: {org_adress}',
        reply_markup=confirm_markup
    )

@bot.callback_query_handler(func=lambda call: call.data in ["save", "edit"])
async def handle_confirmation(callback): # если юзер нажимает Да, то сохраняет в бд
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
        user_states.pop(callback.from_user.id, None)

    elif callback.data == "edit":  # если нажимает изменить, то начинает цикл добавления в бд заново
        await bot.delete_message(
            callback.message.chat.id,
            callback.message.message_id
        )
        await bot.send_message(
            callback.message.chat.id,
            'Введите новое имя:'
        )
        user_states[callback.from_user.id] = 'waiting_for_new_name'
                    # ------------------------- /сохранение Адреса и Имени в бд --------------------------


                            # ------------------------- изменение адреса и имени доставки в бд -------------------
@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == 'waiting_for_new_name')
async def update_username(message):
    global username
    username = message.text
    await bot.send_message(
        message.chat.id,
        'Теперь введите новый адрес:'
    )
    user_states[message.from_user.id] = 'waiting_for_new_address'

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == 'waiting_for_new_address')
async def update_address(message): # ввести новый адрес
    org_adress = message.text
    cur.execute('UPDATE Users SET username=?, org_adress=? WHERE user_id=?',
                (username, org_adress, message.from_user.id))
    con.commit()
    await bot.send_message(
        message.chat.id,
        "Ваши данные успешно обновлены."
    )
    user_states.pop(message.from_user.id, None)

async def display_user_data(message, user_data): # вывод имени и адреса 
    message_markup = types.InlineKeyboardMarkup()
    change_btn = types.InlineKeyboardButton(text="Изменить", callback_data="edit")
    message_markup.add(change_btn)

    await bot.send_message(            # формирование сообщения
        message.chat.id,
        f'Ваши данные:\nИмя: {user_data[2]}\nАдрес: {user_data[3]}',
        reply_markup=message_markup
    )

@bot.callback_query_handler(func=lambda call: True)
async def handle_callback(callback: types.CallbackQuery):
    order = []
    if callback.data == "order_done":        # при нажатии /Оформить заказ
        cur.execute(f'SELECT * FROM Users WHERE user_id={callback.from_user.id}') # запрос в бд для адреса и имени по user_id
        rows = cur.fetchall()
        order_to_chat = ""   # фомирование сообщения заказа
        print(rows)
        order_to_chat += f"Новый Заказ\n{await display_zakaz(callback.from_user.id)}\n\nАдрес: {rows[0][3]}\nИмя: {rows[0][2]}"
        await bot.send_message(POVAR_CHAT_ID, order_to_chat)        # отправление в поварской чат заказа
        print(callback)
        await bot.delete_message(
            callback.message.chat.id,
            callback.message.id
            )
        
        del user_orders[callback.from_user.id]
        print(user_orders)
        
    elif callback.data in ["plus", "minus"]:        # При нажатии плюс или минус в сообщения меняет кол-во определенной позиции
        product_name = callback.message.caption[:int(callback.message.caption.index("\n"))]
        text = callback.message.caption
        quantity_product = r'Кол-во:\s*(\d+)'    # берет сообщения и определяет имеющееся кол-во
        match = re.search(quantity_product, text)
        for item in range(len(menu)):
            if menu[item]["name"] == product_name:    # ищет название товара в menu.py
                cost = menu[item]["cost"] # берет цену из menu.py
        if match:
            quantity = int(match.group(1))

            if callback.data == "plus" and quantity >= 0:    # если нажата кнопка плюс, то изменяет сообщения в котором кол-во будет на 1 больше 
                quantity += 1
                edit_text = f"{product_name}\nЦена: {cost}\nКол-во: {quantity}"
                if product_name not in order:   # если названия товара нет в текущем заказе, то добавляет его
                    order.append(product_name)
                    order.append(1)
                    for item in range(len(menu)):
                        if menu[item]["name"] == product_name:
                            order.append(cost) 
                            break
                else:      # если название есть, то просто меняет кол-во
                    for i in range(0, len(order)):
                        if order[i] == product_name:
                            order[i + 1] += 1
                            break

                print(order) 

            elif callback.data == "minus" and quantity > 0: # тоже, что и выше, только с минусом
                quantity -= 1
                edit_text = f"{product_name}\nЦена: {cost}\nКол-во: {quantity}" 

                for i in range(len(order)):
                    if order[i] == product_name:
                        order[i + 1] -= 1     
                        if order[i + 1] == 0:   # если кол-ва в заказе настает 0, то удаляет из текущего заказа совсем
                            del order[i:i + 3]
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
            user_orders[callback.from_user.id] = order
        elif callback.from_user.id in user_orders:
            for item in range(len(menu)):
                if menu[item]["name"] == product_name:
                    cost = menu[item]["cost"]
            if match:
                quantity = int(match.group(1))

                if callback.data == "plus" and quantity >= 0:   # разделение zakaz для каждого пользователя свой, без этих строк у всех пользователей только один заказ 
                    quantity += 1
                    edit_text = f"{product_name}\nЦена: {cost}\nКол-во: {quantity}"
                    if product_name not in user_orders[callback.from_user.id]:
                        user_orders[callback.from_user.id].append(product_name)
                        user_orders[callback.from_user.id].append(1)
                        for item in range(len(menu)):
                            if menu[item]["name"] == product_name:
                                user_orders[callback.from_user.id].append(cost) 
                                break
                    else:
                        for i in range(0, len(user_orders[callback.from_user.id])):
                            if user_orders[callback.from_user.id][i] == product_name:
                                user_orders[callback.from_user.id][i + 1] += 1
                                break
        print(user_orders)
        msg_markup = types.InlineKeyboardMarkup()
        plus_btn = types.InlineKeyboardButton(text="+", callback_data="plus")
        minus_btn = types.InlineKeyboardButton(text="-", callback_data="minus")
        msg_markup.add(minus_btn, plus_btn)

        await bot.edit_message_caption(       # изменение сообщения в ассортименте, для того чтобы менять "Кол-во: "
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=edit_text,
            reply_markup=msg_markup
        )


@bot.message_handler(commands=["Оформить"])
async def get_zakaz(message):
    cur.execute(f'SELECT * FROM Users WHERE user_id={message.from_user.id}')
    rows = cur.fetchall()
    if rows != []:
        msg_markup = types.InlineKeyboardMarkup()
        order_btn = types.InlineKeyboardButton(text="Все верно", callback_data="zakaz_done")
        msg_markup.add(order_btn)
        if message.from_user.id in user_orders:    # если человек нажимал что заказать, то сообщение что он заказал
            print(message)
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
    else:
        await bot.send_message(  # если челика нет в бд, то просит ввести адрес и имя
            message.chat.id,
            "Для заказа необходимо ввести адрес"
        )

async def display_zakaz(id):   # красивый вывод всего заказа в сообщение
    order = user_orders[id]
    out = ""  # сам заказ весь
    sum = 0
    for i in range(0, len(order)):
        if type(order[i]) == str:
            out += f"{order[i+1]} - {order[i]} \n"
            sum += order[i+2] * order[i+1]
    out += "Сумма: " + str(sum)

    return out


asyncio.run(bot.polling())
