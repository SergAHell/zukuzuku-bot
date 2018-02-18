#coding: utf8

import telebot 
import config
import os
import time
bot = telebot.TeleBot(token = config.token)


files = os.listdir('./pics')
files.sort()
for i in files:
    with open('./pics/'+i, 'rb') as file:
        time.sleep(0.5)
        r = bot.send_photo(303986717, file, caption='<b>test<b>', parse_mode='HTML') 
        