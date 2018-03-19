#coding: utf8

import  config
import telebot
import api

bot = telebot.TeleBot(token = config.token)

print(api.escape_string(bytes('\test')))

bot.send_message(
    303986717,
    api.get_most_popular_chats(),
    parse_mode='HTML'
)