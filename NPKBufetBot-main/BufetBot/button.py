import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types

async def send_menu(): 
    keyboard_buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
    assortment_button = types.KeyboardButton("/Ассортимент")
    adress_button = types.KeyboardButton("/Адрес Доставки")
    order_button = types.KeyboardButton("/Оформить заказ")
    keyboard_buttons.add(assortment_button, adress_button)
    keyboard_buttons.add(order_button)

async def assortiment():  # отправление всего меню из menu.py
    message_markup_assortment = types.InlineKeyboardMarkup() # кнопки В СООБЩЕНИЕ минус/плюс для кол-ва позиции 
    plus_button = types.InlineKeyboardButton(text="+", callback_data="plus")
    minus_button = types.InlineKeyboardButton(text="-", callback_data="minus")
    message_markup_assortment.add(minus_button, plus_button)


async def save_address(): # сохранение адреса заказчика в бд
    confirm_markup = types.InlineKeyboardMarkup()
    yes_btn = types.InlineKeyboardButton(text="Да", callback_data="save")
    confirm_markup.add(yes_btn)

async def display_user_data(): # вывод имени и адреса 
    message_markup = types.InlineKeyboardMarkup()
    change_btn = types.InlineKeyboardButton(text="Изменить", callback_data="edit")
    message_markup.add(change_btn)

async def get_zakaz():
        msg_markup = types.InlineKeyboardMarkup()
        order_btn = types.InlineKeyboardButton(text="Все верно", callback_data="zakaz_done")
        msg_markup.add(order_btn)