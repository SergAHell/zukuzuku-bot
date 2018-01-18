# coding: utf8

import telebot
import logging
import ujson
import re
import sqlite3

bot = telebot.TeleBot(token = '495038140:AAHVdOnVja8EEb9LR8qlmhsCbRiS2imSkC4')

logging.basicConfig(
                    format='%(filename)s [LINE:%(lineno)-3d]# %(levelname)-8s - %(name)-9s [%(asctime)s] - %(message)-50s ',
                    datefmt='%m/%d/%Y %I:%M:%S %p'
)

restricted_stickers = [
    'CAADBAADAgAD5WdgGP8_mtUfmHTUAg',
    'CAADAgADFQAD3kedFhWDQDF4LJsdAg',
    'CAADAgADJgAD3kedFjtizHvpvTKGAg'
]

restricted_packs = [
    's408971237_by_fStikBot',
    'konfaleto2016'
]

def bot_send(msg):
    mesg = '```\n%s\n```' % ujson.dumps(msg, indent = 4, ensure_ascii=False)
    strs = re.split('\n', mesg)
    number = -1
    srts = []
    for i in strs:
        if i[-5::] != 'null,':
            number = number + 1
            srts.append(i)
    number = -1      
    mesg = ''      
    for i in srts:
        mesg = mesg + i + '\n'
    bot.send_message(msg.chat.id, mesg, parse_mode='Markdown')


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

def add_to_DB(msg):
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM db WHERE `StickerFileID` = "{}" and `GroupID` = "{}"'.format(msg.reply_to_message.sticker.file_id, str(msg.chat.id))
        print(sql)
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is None:
            sql = 'INSERT INTO db VALUES("{}","{}")'.format(str(msg.chat.id), msg.reply_to_message.sticker.file_id)
            cursor.execute(sql)
            conn.commit()

@bot.message_handler(commands = ['sticker_ban'])
def bot_sticker_ban(msg):
    for i in bot.get_chat_administrators(msg.chat.id):
        if msg.from_user.id == i.user.id:
            try:
                if msg.reply_to_message.content_type == 'sticker':
                    message = msg
                    add_to_DB(msg)
                    stri = r'/sticker_unban {0}'.format(msg.reply_to_message.sticker.file_id)
                    print(stri)
                    bot.reply_to(msg, 'Sticker <b>{0}</b> added to blacklist. To remove it write: \n<code>{1}</code>'.format(msg.reply_to_message.sticker.file_id, stri), parse_mode = 'HTML')
                    bot.delete_message(msg.chat.id, msg.reply_to_message.message_id)
            except Exception as e:
                bot_send(msg)
                logging.error(e)

@bot.message_handler(commands = ['sticker_unban'])
def bot_sticker_unban(msg):
    for i in bot.get_chat_administrators(msg.chat.id):
        if msg.from_user.id == i.user.id:
            try:
                x = re.split(' ', msg.text)
                if len(x) > 2 or len(x) < 2:
                    bot.reply_to(msg, 'Wrong command, try again.')
                else:
                    sticker_id = re.split(' ', msg.text)[1]
                    with DataConn('db.db') as conn:
                        cursor = conn.cursor()
                        sql = 'SELECT * FROM db WHERE `StickerFileID` = "{}" and `GroupID` = "{}"'.format(x[1], str(msg.chat.id))
                        cursor.execute(sql)
                        res = cursor.fetchone()
                        if res is not None:
                            sql = 'DELETE FROM db WHERE `StickerFileID` = "{}" and `GroupID` = "{}"'.format(x[1], str(msg.chat.id))
                            cursor.execute(sql)
                            conn.commit()
                            bot.reply_to(msg, 'Sticker <b>{}</b> removed from DB.'.format(x[1]), parse_mode = 'HTML')
                        else:
                            bot.reply_to(msg, "This sticker doesn't exist in DB. You must ban it to be able to unban it.")
            except Exception as e:
                logging.error(e)

@bot.message_handler(content_types = ['sticker'])
def bot_del(msg):
    message = msg
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM db WHERE `StickerFileID` = "{}" and `GroupID` = "{}"'.format(msg.sticker.file_id, str(msg.chat.id))
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is not None:
            bot.delete_message(msg.chat.id, message.message_id)

@bot.message_handler(content_types = ['text'], func = lambda msg: msg.text == 'nsdfjkgvsdhipjh')
def bot_answ(msg):
    message = msg
    bot.send_message(msg.chat.id, msg.chat.id)

while True:
    try:        
        bot.polling(none_stop = True)
    except Exception as e:
        logging.error(e)
