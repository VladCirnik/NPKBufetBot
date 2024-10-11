import telebot
from telebot import types
from menu import menu
import sqlite3

API_TOKEN = '7817351008:AAGKEjuJzEFM4WtvSgc8Hieopvkz108uijw'
bot = telebot.TeleBot(API_TOKEN)

connect = sqlite3.connect('users.db')
cur = connect.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS Users (
id INTEGER PRIMARY KEY,
userid INTEGER NOT NULL,
tg_username TEXT NOT NULL,
username TEXT NOT NULL,
org_adress TEXT NOT NULL,
)
''')

connect.commit()