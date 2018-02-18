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


logging.basicConfig(
    format='%(filename)s [LINE:%(lineno)-3d]# %(levelname)-8s - %(name)-9s [%(asctime)s] - %(message)-50s ',
    datefmt='%m/%d/%Y %I:%M:%S %p')

cherrypy.config.update({
    'log.screen': False,
    'log.access_file': '',
    'log.error_file': ''
})


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


def get_user_lang(msg):
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT `Language` FROM users WHERE `UserID` = {}'.format(
            msg.chat.id)
        cursor.execute(sql)
        res = cursor.fetchone()
    return res[0]


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


def register_new_chat(msg):
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM chats WHERE `chat_id` = {}'.format(msg.chat.id)
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is None:
            for i in bot.get_chat_administrators(msg.chat.id):
                if i.status == 'creator':
                    creator_name = i.user.first_name
                    creator_id = i.user.id
                sql = 'SELECT * FROM chatAdmins WHERE `chat_id` = {} AND `AdminID` = {}'.format(
                    msg.chat.id, 
                    i.user.id)
                cursor.execute(sql)
                res = cursor.fetchone()
                if res is None:
                    sql = 'INSERT INTO chatAdmins VALUES ("{}", "{}", "{}", "{}", "{}", "{}")'.format(
                        msg.chat.id, msg.chat.title, i.user.first_name,
                        i.user.id, 0, int(time.time()))
                    cursor.execute(sql)
                    conn.commit()
            sql = 'INSERT INTO chats VALUES ("{}", "{}", "{}", "{}", "{}", "{}", "{}")'.format(
                msg.chat.id, 
                msg.chat.title, 
                creator_name, 
                creator_id,
                bot.get_chat_members_count(msg.chat.id),
                0,
                int(time.time()), 
                )
            cursor.execute(sql)
            conn.commit()
            cursor.execute('SELECT * FROM chats')
            r = cursor.fetchall()
            bot.send_message(
                config.reports_group_id,
                text.service_messages['new_chat'].format(
                    chat_id=msg.chat.id,
                    chat_name=msg.chat.title,
                    chat_amount=len(r),
                    admin_id=creator_id,
                    admin_name=creator_name,
                    chat_users_amount=bot.get_chat_members_count(msg.chat.id)),
                parse_mode='HTML')
            bot.send_message(msg.chat.id, text.group_messages['ru']['start'])
        else:
            for i in bot.get_chat_administrators(msg.chat.id):
                sql = 'SELECT * FROM chatAdmins WHERE `chat_id` = {} AND `AdminID` = {}'.format(
                    msg.chat.id, 
                    i.user.id)
                cursor.execute(sql)
                res = cursor.fetchone()
                if res is None:
                    sql = 'INSERT INTO chatAdmins VALUES ("{}", "{}", "{}", "{}", "{}", "{}")'.format(
                        msg.chat.id, msg.chat.title, i.user.first_name,
                        i.user.id, 0, int(time.time()))
                    cursor.execute(sql)
                    conn.commit()
            sql = 'SELECT `ChatMembersCount` FROM chats WHERE `chat_id` = {chat_id}'.format(
                chat_id=msg.chat.id)
            res = cursor.execute(sql).fetchone()
            if res != bot.get_chat_members_count(msg.chat.id):
                sql = 'UPDATE chats SET `ChatMembersCount` = {members_count} WHERE `chat_id` = {chat_id}'.format(
                    members_count=bot.get_chat_members_count(msg.chat.id),
                    chat_id=msg.chat.id)
                cursor.execute(sql)
                conn.commit()


def register_new_user(call, lang):
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM users WHERE UserID = {}'.format(
            int(call.from_user.id))
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is None:
            try:
                surname = call.from_user.last_name
            except Exception as e:
                logging.error(e)
                surname = 'Unknown{}'.format(call.from_user.id)
            sql = 'INSERT INTO users VALUES("{}", "{}", "{}", "{}", "{}", "{}")'.format(
                int(call.from_user.id), int(time.time()),
                str(call.from_user.first_name), surname, 0, lang)
            cursor.execute(sql)
            conn.commit()
            cursor.execute('SELECT * FROM users')
            r = cursor.fetchall()
            bot.send_message(
                config.reports_group_id,
                text.service_messages['new_user'].format(
                    user_id=call.from_user.id,
                    user_name=call.from_user.first_name,
                    user_amount=len(r),
                    user_lang = lang
                    ),
                parse_mode='HTML',
                disable_web_page_preview=True)
        else:
            try:
                surname = call.from_user.last_name
            except Exception as e:
                logging.error(e)
                surname = 'Unknown{}'.format(call.from_user.id)
            sql = 'UPDATE users SET `Language` = "{}" WHERE `UserID` = "{}"'.format(
                lang, call.from_user.id)
            print(sql)
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

def del_url(msg):
    signal = False
    try:
        for i in msg.entities:
            if i.type == 'url':
                signal = True
    except Exception as e:
        pass
    finally:
        if signal is True:
            bot.delete_message(
                msg.chat.id,
                msg.message_id
            )
            print('Удалено сообщение с ссылкой')

def create_user_language_keyboard():
    lang_keyboard = types.InlineKeyboardMarkup()
    lang_keyboard.add(types.InlineKeyboardButton(text="Русский", callback_data='ru_lang'))
    lang_keyboard.add(types.InlineKeyboardButton(text="English", callback_data='en_lang'))
    lang_keyboard.add(types.InlineKeyboardButton(text="O'zbek", callback_data='uz_lang'))
    return lang_keyboard

def create_group_language(group_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data='ru_lang'))
    keyboard.add(types.InlineKeyboardButton(text="🇺🇸 English", callback_data='en_lang'))
    keyboard.add(types.InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data='uz_lang'))
    return keyboard

def create_group_settings(msg):
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

def set_setting(set_name, group_id, state):
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'UPDATE chatSettings SET `{set_name}` = {state} WHERE `chatID` = {group_id}'.format(
            set_name = set_name,
            group_id = group_id,
            state = state
        )
        cursor.execute(sql)
        conn.commit()

def get_settings(group_id):
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM chatSetting WHERE `chatID` = {group_id}'.format(
            group_id = group_id
        )
        cursor.execute(sql)
        res = cursor.fecthone()
        return res

@bot.message_handler(commands = ['nsdfjkgvsdhipjh'])
def bot_answ(msg):
    message = msg
    bot.send_message(msg.chat.id, 'test', reply_markup=create_group_settings(msg))

@bot.channel_post_handler(content_types=['text'])
def bot_broadcast(msg):
    bot.forward_message(config.adminID, config.channel_ID, msg.message_id)


@bot.message_handler(commands=['start'], func=lambda msg: msg.chat.type == 'private')
def bot_user_start(msg):
    message = msg
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM users WHERE UserID = {}'.format(msg.from_user.id)
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is None:
            bot.send_message(
                msg.chat.id,
                text.user_messages['start'],
                reply_markup=create_user_language_keyboard()
                )
        else:
            bot.send_message(msg.chat.id, text.user_messages[get_user_lang(msg)]['start'])


@bot.message_handler(commands=['start'], func=lambda msg: msg.chat.type != 'private')
def bot_group_start(msg):
    message = msg
    api.register_new_chat(msg)



@bot.message_handler(commands=['kick'], func=lambda msg: msg.chat.type != 'private')
def bot_kick(msg):
    if utils.check_status(msg):
        bot.kick_chat_member(
            msg.chat.id,
            msg.reply_to_message.from_user.id,
            until_date=str(time.time() + 31)
        )
        bot.unban_chat_member(msg.chat.id, msg.reply_to_message.from_user.id)
        bot.reply_to(msg, text.user_messages['ru']['commands']['kick'].format(
            user=msg.reply_to_message.from_user.first_name,
            user_id=msg.reply_to_message.from_user.id,
            admin=msg.from_user.first_name,
            admin_id=msg.from_user.id), 
            parse_mode = 'HTML'
        )

@bot.message_handler(commands = ['ban', 'ban_me_please'], func = lambda msg: msg.chat.type == 'supergroup')
def bot_ban_me_please(msg):
    if msg.text == '/ban_me_please':
        t = random.randint(1, 10)
        ban_time = 60*t
        try:
            bot.restrict_chat_member(
                msg.chat.id,
                msg.from_user.id,
                until_date=str(time.time() + ban_time))
            bot.send_message(msg.chat.id, text.group_messages['ru']['ban_me_please'].format(
                user_id = msg.from_user.id,
                user_name = msg.from_user.first_name,
                t = t
            ), parse_mode = 'HTML')
        except Exception as e:
            print(e)
    else:
        if utils.check_status(msg):
            bot.kick_chat_member(
                msg.chat.id,
                msg.reply_to_message.from_user.id,
                until_date=str(time.time() + 31708800))
            bot.reply_to(msg, text.user_messages['ru']['commands']['ban'].format(
                user=msg.reply_to_message.from_user.first_name,
                user_id=msg.reply_to_message.from_user.id,
                admin=msg.from_user.first_name,
                admin_id=msg.from_user.id), parse_mode = 'HTML')

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
    register_new_chat(msg)
    curr_greeting = random.choice(text.group_messages['ru']['greetings_file_id'])
    bot.send_photo(
        msg.chat.id,
        photo = curr_greeting,
        caption = text.group_messages['ru']['greetings'][curr_greeting]
    )

@bot.message_handler(commands = ['unban'], func = lambda msg: msg.chat.type != 'private')
def bot_user_unban(msg):
    if utils.check_status(msg):
        if len(msg.text) not in [6, 18]:
            user_id = re.split(' ', msg.text)[len(re.split(' ', msg.text))-1]
            r = bot.get_chat_member(
                msg.chat.id, 
                user_id
            )
            if r.status in ['restricted', 'kicked']:
                bot.restrict_chat_member(
                    msg.chat.id,
                    user_id,
                    can_send_media_messages=True,
                    can_add_web_page_previews=True,
                    can_send_messages=True,
                    can_send_other_messages=True
                )
                bot.send_message(
                    msg.chat.id,
                    text.group_messages['ru']['unbanned'].format(
                        user_id = user_id,
                        user_name = r.user.first_name,
                        admin_id = msg.from_user.id,
                        admin_name = msg.from_user.first_name
                    ), 
                    parse_mode='HTML'
                )
            else:
                bot.send_message(msg.chat.id, text.group_messages['ru']['not_in_ban'].format(
                    user_id = user_id,
                    user_name = r.user.first_name
                ), 
                parse_mode='HTML')

@bot.message_handler(content_types = ['text'], func = lambda msg: msg.chat.id in [-1001078768749, -1001327810437])
def bot_del_url(msg):
    del_url(msg)

@bot.message_handler(commands=['ro'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_users_ro(msg):
    if utils.check_status(msg):
        try:
            if len(msg.text) in [3, 15]:
                ban_time = 60
            else:
                    ban_time = parse_time(msg.text)
                    bot.restrict_chat_member(
                        msg.chat.id,
                        msg.reply_to_message.from_user.id,
                        until_date=str(time.time() + ban_time))
                    bot.send_message(
                        msg.chat.id,
                        '[{}](tg://user?id={}) попросил [{}](tg://user?id={}) помолчать на {} сек.'.format(
                            msg.from_user.first_name, 
                            msg.from_user.id,
                            msg.reply_to_message.from_user.first_name,
                            msg.reply_to_message.from_user.id, 
                            ban_time),
                        parse_mode='Markdown',
                        disable_web_page_preview=True)
        except Exception as e:
            logging.error(e)
            bot.send_message(msg.chat.id, e)
            bot.send_message(msg.chat.id, msg.text)


@bot.message_handler(commands=['stickerpack_ban'],func=lambda msg: msg.chat.type == 'supergroup')
def bot_stickerpack_ban(msg):
    if utils.check_status(msg):
        try:
            if msg.reply_to_message.content_type == 'sticker':
                message = msg
                sticker_packname = None
                try:
                    sticker_packname = msg.reply_to_message.sticker.set_name
                except Exception as e:
                    bot.reply_to(
                        msg,
                        "This sticker don't have stickerpack. I can't ban stickerpack, but i'll ban this sticker"
                    )
                    add_to_DB(msg)
                    stri = r'/sticker_unban {0}'.format(
                        msg.reply_to_message.sticker.file_id
                        )
                    bot.reply_to(
                        msg,
                        'Sticker <b>{0}</b> added to blacklist. To remove it write: \n<code>{1}</code>'.format(
                            msg.reply_to_message.sticker.file_id, 
                            stri
                            ),
                            parse_mode='HTML'
                            )
                if sticker_packname is not None:
                    stickerpack = bot.get_sticker_set(sticker_packname)
                    for i in stickerpack.stickers:
                        ban_sticker(i.file_id, msg.chat.id)
                        stri = r'/stickerpack_unban {}'.format(
                            sticker_packname
                            )
                        bot.send_message(
                            msg.chat.id,
                            'Banned <b>{}</b> stickers. To unban them write: \n<code>{}</code>'.format(
                            len(stickerpack.stickers), 
                            stri
                            ))
        except Exception as e:
            logging.error(e)
            bot.send_message(msg.chat.id, e)


@bot.message_handler(commands=['stickerpack_unban'], func=lambda msg: msg.chat.type != 'private')
def bot_stickerpack_unban(msg):
    if utils.check_status(msg):
        try:
            x = re.split(' ', msg.text)
            if len(x) != 2:
                bot.reply_to(msg, text.group_messages['ru']['wrong_command'])
            else:
                try:
                    for i in bot.get_sticker_set(x[1]).stickers:
                        pass
                except Exception as e:
                    pass
        except Exception as e:
            pass



@bot.message_handler(commands=['sticker_ban'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_sticker_ban(msg):
    if utils.check_status(msg):
        try:
            if msg.reply_to_message.content_type == 'sticker':
                message = msg
                add_to_DB(msg)
                stri = r'/sticker_unban {0}'.format(
                    msg.reply_to_message.sticker.file_id
                    )
                bot.reply_to(
                    msg,
                    'Sticker <b>{0}</b> added to blacklist. To remove it write: \n<code>{1}</code>'.format(
                        msg.reply_to_message.sticker.file_id,
                        stri
                        ),
                        parse_mode='HTML'
                        )
                bot.delete_message(
                    msg.chat.id,
                    msg.reply_to_message.message_id)
        except Exception as e:
            bot_send(msg)
            logging.error(e)


@bot.message_handler(commands=['sticker_unban'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_sticker_unban(msg):
    if utils.check_status(msg):
        try:
            x = re.split(' ', msg.text)
            if len(x) > 2 or len(x) < 2:
                bot.reply_to(msg, 'Wrong command, try again.')
            else:
                sticker_id = re.split(' ', msg.text)[1]
                with DataConn('db.db') as conn:
                    cursor = conn.cursor()
                    sql = 'SELECT * FROM db WHERE `StickerFileID` = "{}" and `GroupID` = "{}"'.format(
                        x[1], 
                        str(msg.chat.id)
                        )
                    cursor.execute(sql)
                    res = cursor.fetchone()
                    if res is not None:
                        sql = 'DELETE FROM db WHERE `StickerFileID` = "{}" and `GroupID` = "{}"'.format(
                            x[1], 
                            str(msg.chat.id)
                            )
                        cursor.execute(sql)
                        conn.commit()
                        bot.reply_to(
                            msg,
                            'Sticker <b>{}</b> removed from DB.'.format(
                                x[1]
                                ),
                            parse_mode='HTML')
                    else:
                        bot.reply_to(
                            msg,
                            "This sticker doesn't exist in DB. You must ban it to be able to unban it."
                        )
        except Exception as e:
            logging.error(e)


@bot.message_handler(
    content_types=['sticker'], 
    func=lambda msg: msg.chat.type == 'supergroup'
    )
def bot_del(msg):
    message = msg
    with DataConn('db.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM db WHERE `StickerFileID` = "{}" and `GroupID` = "{}"'.format(
            msg.sticker.file_id, 
            str(msg.chat.id)
            )
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is not None:
            bot.delete_message(msg.chat.id, message.message_id)


@bot.message_handler(
    commands=['help'], 
    func=lambda msg: msg.chat.type == 'private'
)
def bot_help(msg):
    bot.send_message(
        msg.chat.id,
        text.user_messages[get_user_lang(msg)]['help'],
        parse_mode='HTML')


@bot.message_handler(commands=['about'], func=lambda msg: msg.chat.type == 'private')
def bot_about(msg):
    bot.send_message(
        msg.chat.id,
        text.user_messages[get_user_lang(msg)]['about'],
        parse_mode='Markdown')





@bot.message_handler(content_types=['photo'], func = lambda msg: msg.chat.id == 303986717)
def bot_text(msg):
    bot.reply_to(msg, "<code>'{}': '{}',</code>".format(msg.photo[0].file_id, msg.caption), parse_mode ='HTML')



@bot.callback_query_handler(func=lambda c: c.data[-4:len(c.data)] == 'lang')
def change_language(call):
    lang = call.data[0:2]
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text.user_messages[lang]['chosen_language'])
    register_new_user(call, lang)

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
