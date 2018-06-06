#coding: utf8

import telebot
from progressbar import ProgressBar
import logging
import api
import config

logging.basicConfig(
                    format='%(filename)s [LINE:%(lineno)-3d]# %(levelname)-8s - %(name)-9s [%(asctime)s] - %(message)-50s ',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level = logging.INFO
                    )

message_id = int(input("Айди сообщения для рассылки: "))

bot = telebot.TeleBot(token = config.token)

chats = api.get_all()
pbar = ProgressBar(maxval=len(chats))
pbar.start()
counter = 0
for chat in chats:
    counter += 1
    try:
        bot.forward_message(
            chat['chat_id'],
            -1001384235254,
            message_id
        )
    except Exception as e:
        pass
        try:
            bot.forward_message(
                int(chat['user_id']),
                -1001384235254,
                message_id
            )
        except Exception as e:
            pass
    pbar.update(counter)