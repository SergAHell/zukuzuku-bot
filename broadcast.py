#coding: utf8

import api
import telebot
import config

message_id = int(input())

bot = telebot.TeleBot(token = config.token)

chats = api.get_all()

for chat in chats:
    if chat['settings']['get_notifications'] == '1':
        bot.forward_message(
            int(chat['chat_id']),
            1384235254,
            message_id
        )