#coding: utf8

import sqlite3
import telebot
import logging
import config
import time

logging.basicConfig(
                    format='%(filename)s [LINE:%(lineno)-3d]# %(levelname)-8s - %(name)-9s [%(asctime)s] - %(message)-50s ',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
)

bot = telebot.TeleBot(token = config.token)

class DataConn:
    def __init__(self, db_name):
        self.db_name = db_name
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        if exc_val:
            raise

with DataConn('db.db') as conn:
    cursor = conn.cursor()
    sql = 'SELECT * FROM users'
    cursor.execute(sql)
    res = cursor.fetchall()
    success = 0
    notSuccess = 0
    counter = 0
    for i in res:
        time.sleep(0.2)
        counter +=1
        try:
            bot.forward_message(int(i[0]), -1001384235254, 25)
        except Exception as e:
            logging.error(e)
    sql = 'SELECT * FROM chats'
    cursor.execute(sql)
    res = cursor.fetchall()
    success = 0
    notSuccess = 0
    counter = 0
    for i in res:
        time.sleep(0.2)
        counter +=1
        try:
            bot.forward_message(int(i[0]), -1001384235254, 25)
        except Exception as e:
            logging.error(e)