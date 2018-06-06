#coding: utf8


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
            bot.send_chat_action(int(i[0]), 'typing')
            print('{:>4}/{:>4}|Sending test message to {:>15}'.format(counter, len(res) ,i[0]))
            success += 1
            sql = 'UPDATE users SET `isBlocked` = {} WHERE `UserID` = {}'.format(0,i[0])
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            print('{:>4}/{:>4}|Blocked by user         {:>15}'.format(counter, len(res) ,i[0]))
            notSuccess +=1
            sql = 'UPDATE users SET `isBlocked` = {} WHERE `UserID` = {}'.format(1,i[0])
            cursor.execute(sql)
            conn.commit()
    print('-'*50)
    print('{:>4}/{:>4} users are available   - {}%'.format(success, len(res), round((success/len(res))*100, 1)))
    print('{:>4}/{:>4} users are unavailable - {}%'.format(notSuccess, len(res), round((notSuccess/len(res))*100, 1)))
    