# coding: utf8

import logging
import random
import re
import sqlite3
import time

import telebot
from telebot import types

import api
import cherrypy
import config
import text
import ujson
import utils

WEBHOOK_HOST = '5.9.178.83'
WEBHOOK_PORT = 8443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
# На некоторых серверах придется указывать такой же IP, что и выше
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)

bot = telebot.TeleBot(token=config.token)

telebot_logger = logging.getLogger('telebot')
sqlite_info = logging.getLogger('sqlite')
main_info = logging.getLogger('main_info')
report_info = logging.getLogger('reports')

if __name__ == '__main__':
    log_name = 'logs.txt'
    f = open(log_name,'w')
    f.close()
    print('Файл логов создан')

telebot_logger = logging.getLogger('telebot')
mysql_info = logging.getLogger('mysql')
main_info = logging.getLogger('main_info')
report_info = logging.getLogger('reports')
print('Список логгеров создан')

logging.basicConfig(
                    format='%(filename)s [LINE:%(lineno)-3d]# %(levelname)-8s - %(name)-9s [%(asctime)s] - %(message)-50s ',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level = logging.INFO
                    )


class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
            'content-type' in cherrypy.request.headers and \
                cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

def bot_send(msg):
    mesg = '```\n%s\n```' % ujson.dumps(msg, indent=4, ensure_ascii=False)
    strs = re.split('\n', mesg)
    number = -1
    srts = []
    for i in strs:
        if i[-5:] != 'null,':
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
    file_id = msg.reply_to_message.sticker.file_id
    group_id = msg.chat.id
    ban_sticker(file_id, group_id)


def ban_sticker(file_id, group):
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM db WHERE `StickerFileID` = "{}" and `GroupID` = "{}"'.format(file_id, str(group))
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is None:
            sql = 'INSERT INTO db VALUES("{}","{}")'.format(str(group), file_id)
            cursor.execute(sql)
            conn.commit()

def unban_sticker(sticker, group_ID):
    file_id = sticker.file_id
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM db WHERE `GroupID` = "{group}" AND `StickerFileID` = "{sticker_id}"'.format(
            group=group_ID, 
            sticker_id=file_id)
        res = cursor.execute(sql).fetchone()
        if res is not None:
            sql = 'DELETE FROM db WHERE `StickerFileID` = "{sticker_id}" and `GroupID` = "{group}"'.format(
                group=group_ID, 
                sticker_id=file_id)
            cursor.execute(sql)
            conn.commit()


def parse_time(string):
    l = re.split(' ', string)
    mult = l[1][-1:]
    mult_int = 1
    if mult == 's':
        mult_int = 1
    elif mult == 'm':
        mult_int = 60
    elif mult == 'h':
        mult_int = 60 * 60
    elif mult == 'd':
        mult_int = 60 * 60 * 24
    return int(l[1][:-1:]) * mult_int

def create_user_language_keyboard(referrer=303986717):
    lang_keyboard = types.InlineKeyboardMarkup()
    lang_keyboard.add(types.InlineKeyboardButton(text="Русский", callback_data='ru_{ref}_lang'.format(ref=referrer)))
    lang_keyboard.add(types.InlineKeyboardButton(text="English", callback_data='en_{ref}_lang'.format(ref=referrer)))
    lang_keyboard.add(types.InlineKeyboardButton(text="O'zbek", callback_data='uz_{ref}_lang'.format(ref=referrer)))
    return lang_keyboard

def create_group_language():
    """
    Создает кнопки настройки языка группы
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data='ru_lang'))
    keyboard.add(types.InlineKeyboardButton(text="🇺🇸 English", callback_data='en_lang'))
    keyboard.add(types.InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data='uz_lang'))
    return keyboard

def create_group_settings():
    """
    Создает кнопки настройки группы
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(text="Включить оповещения", callback_data='notify1')
    btn2 = types.InlineKeyboardButton(text="Отключить оповещения", callback_data='notify0')
    keyboard.add(btn1, btn2)
    btn1 = types.InlineKeyboardButton(text="Удалять ссылки", callback_data='del_url1')
    btn2 = types.InlineKeyboardButton(text="Оставлять ссылки", callback_data='del_url0')
    keyboard.add(btn1, btn2)
    btn1 = types.InlineKeyboardButton(text="Удалять системные оповещения", callback_data='del_system1')
    btn2 = types.InlineKeyboardButton(text="Оставлять системные оповещения", callback_data='del_system0')
    keyboard.add(btn1, btn2)
    return keyboard

@bot.channel_post_handler(content_types=['text'], func = lambda msg: msg.chat.id == config.channel_ID)
def bot_broadcast(msg):
    bot.forward_message(config.adminID, msg.chat.id, msg.forward_from_message_id)



@bot.message_handler(commands = ['nsdfjkgvsdhipjh'])
def bot_answ(msg):
    message = msg
    bot.send_message(msg.chat.id, 'test', reply_markup=create_group_settings(msg))
    bot_lang(msg)

@bot.message_handler(commands=['start'], func=lambda msg: msg.chat.type == 'private')
def bot_user_start(msg):
    message = msg
    if utils.is_user_new(msg):
        if utils.have_args(msg):
            words = utils.parse_arg(msg)
            referrer = words[1]
        bot.send_message(
            msg.chat.id,
            text.user_messages['start'],
            reply_markup=create_user_language_keyboard()
            )
    else:
        bot.send_message(msg.chat.id, text.user_messages[utils.get_user_lang(msg)]['start'])


@bot.message_handler(commands=['start'], func=lambda msg: msg.chat.type != 'private')
def bot_group_start(msg):
    message = msg
    api.register_new_chat(msg)

@bot.message_handler(commands=['set_text'], func = lambda msg: msg.chat.type != 'private')
def bot_set_text(msg):
    message = msg
    if len(msg.text) not in [9, 21]:
        new_greeting = msg.text[len(msg.text):msg.entities[0].length:-1][::-1]
        print(new_greeting)
        utils.set_greeting(msg, new_greeting)

@bot.message_handler(commands=['kick'], func=lambda msg: msg.chat.type != 'private')
def bot_kick(msg):
    utils.kick_user(msg)

@bot.message_handler(commands = ['ban', 'ban_me_please'], func = lambda msg: msg.chat.type == 'supergroup')
def bot_ban_me_please(msg):
    if msg.text == '/ban_me_please':
        t = random.randint(1, 10)
        ban_time = 60*t
        try:
            if not utils.check_status(msg):
                bot.restrict_chat_member(
                    msg.chat.id,
                    msg.from_user.id,
                    until_date=str(time.time() + ban_time))
                bot.send_message(msg.chat.id, text.group_messages['ru']['ban_me_please'].format(
                    user_id = msg.from_user.id,
                    user_name = msg.from_user.first_name,
                    t = t
                ), parse_mode = 'HTML')
            else:
                bot.send_message(
                    msg.chat.id,
                    text.group_messages['ru']['user_is_admin'].format(
                        admin_id = msg.from_user.id,
                        admin_name = msg.from_user.first_name
                    ),
                    parse_mode='HTML'
                )
        except Exception as e:
            logging.error(e)
    else:
        utils.ban_user(msg)

@bot.message_handler(commands=['language'], func=lambda msg: msg.chat.type == 'private')
def bot_lang(msg):
    bot.send_message(
        msg.chat.id,
        text.user_messages['start'],
        reply_markup=create_user_language_keyboard())


@bot.message_handler(commands=['ping'])
def bot_ping(msg):
    bot.reply_to(
        msg,
        text.user_messages['ru']['commands']['ping'].format(
            unix_time=int(time.time())
            ),
        parse_mode='HTML'
        )


@bot.message_handler(content_types=['new_chat_members'])
def bot_users_new(msg):
    message = msg
    api.register_new_chat(msg)
    if msg.new_chat_member.id != 495038140:
        r = utils.need_greeting(msg)
        if int(r) == 1:
            text = utils.get_greeting(msg)
            res = utils.check_greeting(text)
            if res:
                bot.send_message(
                    msg.chat.id,
                    text, 
                    parse_mode='Markdown'
                )
        if int(r) == 2:
            utils.standart_greeting(msg)
    
    
@bot.message_handler(commands = ['unban'], func = lambda msg: msg.chat.type != 'private')
def bot_user_unban(msg):
    if utils.check_status(msg) and utils.have_args(msg):
        words = utils.parse_arg(msg)
        user_id = words[1]
        utils.unban_user(msg, user_id)

@bot.message_handler(commands=['ro'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_users_ro(msg):
    if utils.check_status(msg):
        utils.read_only(msg)
    else:
        utils.not_enought_rights(msg)

@bot.message_handler(commands=['stickerpack_ban'],func=lambda msg: msg.chat.type == 'supergroup')
def bot_stickerpack_ban(msg):
    if utils.check_status(msg):
        utils.ban_stickerpack(msg)
    else:
        utils.not_enought_rights(msg)

@bot.message_handler(commands=['stickerpack_unban'], func=lambda msg: msg.chat.type != 'private')
def bot_stickerpack_unban(msg):
    if utils.check_status(msg) and utils.have_args(msg):
        words = utils.parse_arg(msg)
        stickerpack_name = words[1]
        utils.unban_stickerpack(msg, stickerpack_name)


@bot.message_handler(commands=['sticker_ban'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_sticker_ban(msg):
    if utils.check_status(msg):
        sticker_id = msg.sticker.file_id
        utils.ban_sticker(msg, sticker_id)
    elif not utils.check_status(msg):
        utils.not_enought_rights(msg)


@bot.message_handler(commands=['sticker_unban'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_sticker_unban(msg):
    if utils.have_args(msg) and utils.check_status(msg):
        sticker_id = utils.parse_arg(msg)
        utils.unban_sticker(msg, sticker_id)
    elif check_status(msg) and not utils.have_args(msg):
        utils.not_enought_rights(msg)
    elif utils.have_args(msg) and not check_status(msg):
        utils.no_args(msg)

@bot.message_handler(content_types=['sticker'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_del(msg):
    utils.del_sticker(msg)


@bot.message_handler(commands=['help'], func=lambda msg: msg.chat.type == 'private')
def bot_help(msg):
    bot.send_message(
        msg.chat.id,
        text.user_messages[utils.get_user_lang(msg)]['help'],
        parse_mode='HTML')


@bot.message_handler(commands=['about'], func=lambda msg: msg.chat.type == 'private')
def bot_about(msg):
    bot.send_message(
        msg.chat.id,
        text.user_messages[utils.get_user_lang(msg)]['about'],
        parse_mode='Markdown')





@bot.message_handler(content_types=['photo'], func = lambda msg: msg.chat.id == 303986717)
def bot_text(msg):
    bot.reply_to(msg, "<code>'{}': '{}',</code>".format(msg.photo[0].file_id, msg.caption), parse_mode ='HTML')



# Кнопки

@bot.callback_query_handler(func=lambda c: c.data[-4:len(c.data)] == 'lang')
def change_language(call):
    words = re.split('_', call.data)
    lang = words[0]
    referer = words[0]
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text.user_messages[lang]['chosen_language'])
    api.register_new_user(call, lang)
    utils.new_referral(msg, referer)

@bot.callback_query_handler(func = lambda c: len(c.data) == 7 and c.data[0:6] == 'notify')
def notify_change(c):
    decision = c.data[-1]
    if utils.check_status(c.message):
        api.set_param(c.message, 'get_notifications', decision)

@bot.callback_query_handler(func = lambda c: len(c.data) == 8 and c.data[0:7] == 'del_url')
def del_url(c):
    decision = c.data[-1]
    if utils.check_status(c.message):
        api.set_param(c.message, 'delete_url', decision)

@bot.callback_query_handler(func = lambda c: len(c.data) == 11 and c.data[0:10] == 'del_system')
def del_system(c):
    decision = c.data[-1]
    if utils.check_status(c.message):
        api.set_param(c.message, 'delete_system', decision)


# Вебхук

bot.remove_webhook()

bot.set_webhook(
    url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
    certificate=open(WEBHOOK_SSL_CERT, 'r'))

cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
