# coding: utf8

import telebot
import config

bot = telebot.TeleBot(token = config.token)

bot.forward_message(303986717, -1001384235254, 9)