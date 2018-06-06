# coding: utf8

import telebot
import config
import time

bot = telebot.TeleBot(token = config.token, threaded = False)

while True:
    bot.send_document(-1001236256304, open('logs.txt', 'rb'))
    time.sleep(86400)