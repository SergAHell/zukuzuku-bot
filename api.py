#coding: utf8

import hashlib
import logging
import time

import pymysql
import pymysql.cursors
import requests
import telebot

import config
import settings
import ujson
import utils

bot = telebot.TeleBot(token = config.token)

class DB:
    def __init__(self, host, user, db, password):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.charset = 'utf8mb4'
        self.cursorclass = pymysql.cursors.DictCursor

class DataConn:
    def __init__(self, db_obj):
        self.host = db_obj.host
        self.user = db_obj.user
        self.password = db_obj.password
        self.db = db_obj.db
        self.charset = db_obj.charset
        self.cursorclass = db_obj.cursorclass

    def __enter__(self):
        self.conn = pymysql.connect(
            host = self.host,
            user = self.user,
            password = self.password,
            db = self.db,
            charset = self.charset,
            cursorclass = self.cursorclass
        )
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        if exc_val:
            raise
db = DB(
    host = config.host,
    user = config.user,
    password = config.password,
    db = config.db
)

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
                    filename = 'logs.txt',
                    level = logging.INFO
                    )


def replacer(text):
    text_list = list(text)
    for i in range(len(text)):
        if text_list[i] in config.restricted_characters:
            text_list[i] = config.restricted_characters_replace[text_list[i]]
    return ''.join(text_list)



def register_admins(msg):
    chat_id = msg.chat.id
    with DataConn(db) as conn:
        cursor = conn.cursor()
        for i in bot.get_chat_administrators(chat_id):
            sql = 'SELECT * FROM `chat_admins` WHERE `admin_id` = {user_id} AND `chat_id` = {chat_id}'.format(
                user_id = i.user.id,
                chat_id = chat_id
            )
            cursor.execute(sql)
            res = cursor.fetchone()
            if res is None:
                sql = 'INSERT INTO `chat_admins` (`chat_id`, `chat_name`, `admin_name`, `admin_id`, `status`) VALUES ("{}", "{}", "{}", "{}", "{}")'.format(
                    chat_id,
                    msg.chat.title,
                    escape_string(i.user.first_name),
                    i.user.id,
                    i.status
                )
                cursor.execute(sql)
                conn.commit()
        

def ban_sticker(msg, sticker_id):
    """
    Банит стикер\n
    :param msg:\n
    :param sticker_id:\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `banned_stickers` WHERE `chat_id` = "{id}" AND `sticker_id` = "{sticker_id}"'.format(
            id = msg.chat.id,
            sticker_id = sticker_id
        )
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is None:
            sql = 'INSERT INTO `banned_stickers`(`chat_id`, `chat_name`, `sticker_id`, `ban_time`) VALUES ("{chat_id}", "{chat_name}", "{sticker_id}", "{ban_time}")'.format(
                chat_id = msg.chat.id,
                chat_name = msg.chat.title,
                sticker_id = sticker_id,
                ban_time = int(time.time())
            )
            sql = sql
            try:
                cursor.execute(sql)
                conn.commit()
            except Exception as e:
                print(sql)
                print(e)
        else:
            if res != msg.chat.title:
                sql = 'SELECT * FROM `banned_stickers` WHERE `chat_id` = "{id}"'.format(
                    id = msg.chat.id
                )
                sql = sql
                cursor.execute(sql)
                res = cursor.fetchall()
                for i in res:
                    sql = 'UPDATE `banned_stickers` SET `chat_name` = "{chat_name}" WHERE `chat_id` = "{id}"'.format(
                        chat_name = msg.chat.title,
                        id = msg.chat.id
                    )
                    sql = sql
                    cursor.execute(sql)
                    conn.commit()

def unban_sticker(msg, sticker_id):
    """
    Разбанивает стикер\n
    :param msg:\n
    :param sticker_id:\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `banned_stickers` WHERE `chat_id` = "{id}" and `sticker_id` = "{sticker_id}"'.format(
            id = msg.chat.id,
            sticker_id = sticker_id
        )
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is not None:
            sql = 'DELETE FROM `banned_stickers` WHERE `chat_id` = "{id}" AND `sticker_id` = "{sticker_id}"'.format(
                id = msg.chat.id,
                sticker_id = sticker_id
            )
            sql = sql
            cursor.execute(sql)
            conn.commit()
            return True
        else:
            return False

def get_creator(msg):
    """
    Возвращает объект создателя чата\n
    :param msg:\n
    """
    creator = bot.get_chat_administrators(msg.chat.id)[0].user
    for i in bot.get_chat_administrators(msg.chat.id):
        if i.status == 'creator':
            creator = i.user
    return creator

def register_new_user(call, lang):
    """
    Регистрирует нового пользователя\n
    :param call:\n
    :param lang:\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM users WHERE `user_id` = {id}'.format(
            id = call.from_user.id
        )
        cursor.execute(sql)
        res = cursor.fetchone()
        sec_name = 'None'
        try:
            sec_name = call.from_user.second_name
        except Exception as e:
            sec_name = 'None'
            logging.error(e)
        if res is None:
            sql = 'INSERT INTO `users` (`user_id`, `registration_time`, `first_name`, `second_name`, `language`) VALUES ("{id}", "{curr_time}", "{first_name}", "{second_name}", "{lang}")'.format(
                id = call.from_user.id,
                curr_time = int(time.time()),
                first_name = escape_string(call.from_user.first_name),
                second_name = escape_string(sec_name),
                lang = lang
            )
            cursor.execute(sql)
            conn.commit()
            sql = 'INSERT INTO `user_settings` (`user_id`, `registration_time`, `language`) VALUES ("{id}", "{curr_time}", "{language}")'.format(
                id = call.from_user.id,
                curr_time = int(time.time()),
                language = lang
            )
            cursor.execute(sql)
            conn.commit()
            utils.notify_new_user(call)
        else:
            sql = 'UPDATE `user_settings` SET `language` = "{lang}" WHERE `user_id` = "{id}"'.format(
                lang = lang,
                id = call.from_user.id
            )
            cursor.execute(sql)
            conn.commit()

def register_new_chat(msg):
    """
    Регистрирует новый чат\n
    :param msg:\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM chats WHERE `chat_id` = {id}'.format(
            id = msg.chat.id
        )
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is None:
            creator = get_creator(msg)
            sql = """INSERT INTO `chats` (`db_id`, `chat_id`, `chat_name`, `creator_name`, `creator_id`, `chat_members_count`, `registration_time`, `settings`) VALUES ("{db_id}", "{chat_id}", "{chat_name}", "{creator_name}", "{creator_id}", "{count}", "{curr_time}", '{settings}')""".format(
                db_id = int(get_chats_count())+1,
                chat_id = msg.chat.id,
                chat_name = escape_string(msg.chat.title),
                creator_name = escape_string(creator.first_name),
                creator_id = creator.id,
                count = bot.get_chat_members_count(msg.chat.id),
                curr_time = int(time.time()),
                settings = ujson.dumps(config.default_group_settings)
            )
            sql = sql
            try:
                cursor.execute(sql)
                conn.commit()
            except Exception as e:
                logging.error('error')
                logging.error(sql)
            sql = 'INSERT INTO `group_settings` (`chat_id`, `language`, `get_notifications`, `greeting`, `delete_url`, `delete_system`) VALUES ("{chat_id}", "{language}", "{get_notifications}", "{greeting}", "{delete_url}", "{delete_system}")'.format(
                chat_id = msg.chat.id,
                language = 'ru',
                get_notifications = 1,
                greeting = r'ТЕСТОВОЕ ОПОВЕЩЕНИЕ',
                delete_url = 0,
                delete_system = 1
            )
            sql = sql
            try:
                cursor.execute(sql)
                conn.commit()
            except Exception as e:
                logging.error('error')
                logging.error(sql)
            utils.notify_new_chat(msg)
            register_admins(msg)
        else:
            sql = 'INSERT INTO `group_settings` (`chat_id`, `language`, `get_notifications`, `greeting`, `delete_url`, `delete_system`) VALUES ("{chat_id}", "{language}", "{get_notifications}", "{greeting}", "{delete_url}", "{delete_system}")'.format(
                chat_id = msg.chat.id,
                language = 'ru',
                get_notifications = 1,
                greeting = r'ТЕСТОВОЕ ОПОВЕЩЕНИЕ',
                delete_url = 0,
                delete_system = 1
            )
            sql = sql
            try:
                cursor.execute(sql)
                conn.commit()
            except Exception as e:
                logging.error('error')
                logging.error(sql)
            register_admins(msg)

def get_users_count():
    """
    Возвращает количество пользователей в базе\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM users'
        cursor.execute(sql)
        res = cursor.fetchall()
        return len(res)

def get_chats_count():
    """
    Возвращает количество чатов в базе\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT COUNT(chat_id) FROM chats'
        cursor.execute(sql)
        res = cursor.fetchone()
        return res['COUNT(chat_id)']

def get_user_param(user_id, column):
    """
    Возвращает определенный параметр пользовательских настроек
    :param msg:
    :param column:
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT `{column}` FROM `user_settings` WHERE `user_id` = "{id}"'.format(
            column = column,
            id = user_id
        )
        sql = sql
        cursor.execute(sql)
        res = cursor.fetchone()
        return res[column]

def get_user_params(user_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT `settings` FROM `users` WHERE `user_id` = "{user_id}"'.format(
            user_id = user_id
        )
        cursor.execute(sql)
        res = cursor.fetchone()
        return res

def set_user_param(user_id, column, state):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'UPDATE `user_settings` SET `{column}` = "{state}" WHERE `user_id` = "{id}"'.format(
            column = column,
            state = state,
            id = user_id
        )
        sql = sql
        cursor.execute(sql)
        conn.commit()

def get_group_params(chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT `settings` FROM `chats` WHERE `chat_id` = {}'.format(chat_id)
        cursor.execute(sql)
        res = cursor.fetchone()
        return ujson.loads(res['settings'])

def change_group_params(chat_id, new_params):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = '''UPDATE `chats` SET `settings` = '{params}' WHERE `chat_id` = {chat_id}'''.format(
            params = new_params,
            chat_id = chat_id
        )
        try:
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            print(e)
            print(sql)

def is_user_new(msg):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM users WHERE `user_id` = "{id}"'.format(
            id = msg.from_user.id
        )
        sql = sql
        cursor.execute(sql)
        r = cursor.fetchone()
        if r is None:
            res = True
        else:
            res = False
        return res

def check_sticker(sticker_id, chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `banned_stickers` WHERE `sticker_id` = "{sticker}" AND `chat_id` = "{chat}"'.format(
            sticker = sticker_id,
            chat = chat_id
        )
        cursor.execute(sql)
        r = cursor.fetchone()
        if r is None:
            return False
        else:
            return True

def get_warns(user_id, chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `warns` WHERE `user_id` = "{user_id}" AND `chat_id` = "{chat_id}"'.format(
            user_id = user_id,
            chat_id = chat_id
        )
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is None:
            sql = 'INSERT INTO `warns`(`user_id`, `chat_id`, `warns`) VALUES ("{user_id}","{chat_id}","{warns}")'.format(
                user_id = user_id,
                chat_id = chat_id,
                warns = 0
            )
            warns = 0
            cursor.execute(sql)
            conn.commit()
        else:
            warns = int(res['warns'])
        return warns

def new_warn(user_id, chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        warns = get_warns(user_id, chat_id)
        warns += 1
        set_warns(user_id, chat_id, warns)

def zeroing_warns(user_id, chat_id):
    set_warns(user_id, chat_id, 0)

def set_warns(user_id, chat_id, warns):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'UPDATE `warns` SET `warns` = "{warns}" WHERE `user_id` = "{user_id}" AND `chat_id` = "{chat_id}"'.format(
            warns = warns,
            user_id = user_id,
            chat_id = chat_id
        )
        cursor.execute(sql)
        conn.commit()


def get_all():
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `chats` ORDER BY `registration_time` ASC'
        cursor.execute(sql)
        return cursor.fetchall()

def change_p(group_id, db_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'UPDATE `chats` SET `db_id` = {} WHERE `chat_id` = {}'.format(
            db_id,
            group_id
        )
        cursor.execute(sql)
        conn.commit()

def replacerr(text):
    text_list = list(text) 
    for idx, word in enumerate(text):
        if word in config.restricted_characters:
            text_list[idx] = config.restricted_characters_replace[word]
    return ''.join(text_list)

def escape_string(value):
    # value = value.replace('\\', r'\\\\')
    # value = value.replace('\0', r'\\0')
    # value = value.replace('\n', r'\\n')
    # value = value.replace('\r', r'\\r')
    # value = value.replace('\032', r'\\Z')
    value = value.replace("'", r"\'")
    value = value.replace('"', r'\"')
    return value

def update_members(user_id, chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'INSERT INTO `chat_users` (`chat_id`, `user_id`, `registration_time`) '

def update_stats_bot(count):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'INSERT INTO `stats` (`amount`, `check_time`) VALUES ("{count}", "{curr_time}")'.format(
            count = count,
            curr_time = int(time.time())
        )
        cursor.execute(sql)
        conn.commit()

def delete_pending():
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'DELETE * FROM `stats`'
        cursor.execute(sql)
        conn.commit()

def check_global_ban(user_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `global_bans` WHERE `user_id` = "{user_id}"'.format(
            user_id = user_id
        )
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is None:
            return False
        else:
            return True

def global_ban(user_id):
    with DataConn(db) as conn:
        if not check_global_ban(user_id):
            cursor = conn.cursor()
            sql = 'INSERT INTO `global_bans` (`user_id`) VALUES  ("{user_id}")'.format(
                user_id = user_id
            )
            cursor.execute(sql)
            conn.commit()

def global_unban(user_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'DELETE FROM `global_bans` WHERE `user_id` = "{user_id}"'.format(
            user_id = user_id
        )
        cursor.execute(sql)
        conn.commit()

def new_update(msg, end_time):
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'INSERT INTO `proceeded_updates` (`user_id`, `chat_id`, `msg_time`, `used_time`, `proceeded_at`) VALUES ("{user_id}", "{chat_id}", "{msg_time}", "{proceeding_time}", "{curr_time}")'.format(
            user_id = user_id,
            chat_id = chat_id,
            msg_time = msg.date,
            proceeding_time = end_time*1000,
            curr_time = int(time.time())
        )
        cursor.execute(sql)
        conn.commit()
    new_content(msg)
    update_chat_stats(msg)
    update_user_stats(msg)

def update_user_stats(msg):
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    chat_name = msg.chat.title
    user_name = msg.from_user.first_name
    with DataConn(db) as conn:
        cursor = conn.cursor()
        current_updates = get_user_messages_count(user_id, chat_id)
        sql = 'SELECT * FROM `most_active_users` WHERE `user_id` = %s AND `chat_id` = %s'
        cursor.execute(sql, (user_id, chat_id))
        res = cursor.fetchone()
        if res is None:
            sql = 'INSERT INTO `most_active_users` (`user_id`, `user_name`, `chat_id`, `chat_name`, `amount`) VALUES (%s, %s, %s, %s, %s)'
            cursor.execute(sql, (user_id, user_name, chat_id, chat_name, current_updates))
            conn.commit()
        else:
            sql = 'UPDATE `most_active_users` SET `user_name` = %s, `amount` = %s WHERE `user_id` = %s'
            cursor.execute(sql, (user_name, current_updates, user_id))
            conn.commit()
        

def get_user_messages_count(user_id, chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT COUNT(user_id) FROM `proceeded_messages` WHERE `chat_id` = "{chat_id}" AND `user_id` = "{user_id}"'.format(
            chat_id = chat_id,
            user_id = user_id
        )
        cursor.execute(sql)
        res = cursor.fetchone()
        return res['COUNT(user_id)']

def update_chat_stats(msg):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        current_updates = get_chat_updates_count(msg.chat.id)
        sql = 'SELECT * FROM `most_popular_chats` WHERE `chat_id` = "{chat_id}"'.format(
            chat_id = msg.chat.id
        )
        cursor.execute(sql)
        res = cursor.fetchone()
        if res is None:
            sql = 'INSERT INTO `most_popular_chats` (`updates_count`, `chat_id`, `chat_name`, `last_update`) VALUES ("{updates}", "{chat_id}", "{chat_name}", "{last_update}")'.format(
                updates = current_updates,
                chat_id = msg.chat.id,
                chat_name = escape_string(msg.chat.title),
                last_update = msg.date
            )
            cursor.execute(sql)
            try:
                conn.commit()
            except Exception as e:
                logging.error(e)
                logging.error(sql)
        else:
            sql = 'UPDATE `most_popular_chats` SET `updates_count` = "{updates}", `chat_name` = "{chat_name}", `last_update` = "{last_update}" WHERE `chat_id` = "{chat_id}"'.format(
                updates = current_updates,
                chat_name = escape_string(msg.chat.title),
                last_update = msg.date,
                chat_id = msg.chat.id
            )
            cursor.execute(sql)
            try:
                conn.commit()
            except Exception as e:
                logging.error(e)
                logging.error(sql)

def get_chat_updates_count(chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT COUNT(chat_id) FROM `proceeded_updates` WHERE `chat_id` = "{chat_id}"'.format(
            chat_id = chat_id
        )
        cursor.execute(sql)
        res = cursor.fetchone()
        return int(res['COUNT(chat_id)'])

def get_most_popular_chats():
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `most_popular_chats` WHERE `chat_id` = "-1001303648604"'
        cursor.execute(sql)
        res = cursor.fetchone()
        r = ujson.dumps(res)
        return r

def get_file_size(msg):
    res = 0
    if msg.content_type == 'audio':
        res = msg.audio.file_size
    elif msg.content_type == 'document':
        res = msg.document.file_size
    elif msg.content_type == 'photo':
        res = msg.photo[-1].file_size
    elif msg.content_type == 'sticker':
        res = msg.sticker.file_size
    elif msg.content_type == 'video':
        res = msg.audio.file_size
    elif msg.content_type == 'video_note':
        res = msg.audio.file_size
    elif msg.content_type == 'voice':
        res = msg.voice.file_size
    return res

def get_file_id(msg):
    res = ''
    if msg.content_type == 'audio':
        res = msg.audio.file_id
    elif msg.content_type == 'document':
        res = msg.document.file_id
    elif msg.content_type == 'photo':
        res = msg.photo[-1].file_id
    elif msg.content_type == 'sticker':
        res = msg.sticker.file_id
    elif msg.content_type == 'video':
        res = msg.audio.file_id
    elif msg.content_type == 'video_note':
        res = msg.audio.file_id
    elif msg.content_type == 'voice':
        res = msg.voice.file_id
    return res


def new_message(msg):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'INSERT INTO `proceeded_messages` (`user_id`, `chat_id`, `content_type`) VALUES ("{user_id}", "{chat_id}", "{cont_type}")'.format(
            user_id = msg.from_user.id,
            chat_id = msg.chat.id,
            msg_time = msg.date,
            cont_type = msg.content_type
        )
        cursor.execute(sql)
        conn.commit()

def new_member(msg):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'INSERT INTO `new_chat_members` (`user_id`, `chat_id`, `joined_chat_at`) VALUES ("{user_id}", "{chat_id}", "{joined_chat_at}")'.format(
            user_id = msg.new_chat_member.id,
            chat_id = msg.chat.id,
            joined_chat_at = msg.date
        )
        cursor.execute(sql)
        conn.commit()

def new_content(msg):
    if msg.content_type == 'text':
        new_message(msg)
    elif msg.content_type == 'new_chat_members':
        new_member(msg)
    else:
        try:
            with DataConn(db) as conn:
                cursor = conn.cursor()
                sql = 'INSERT INTO `{cont_type}` (`user_id`, `chat_id`, `file_id`, `file_size`) VALUES ("{user_id}", "{chat_id}", "{file_id}", "{file_size}")'.format(
                    cont_type = msg.content_type,
                    user_id = msg.from_user.id,
                    chat_id = msg.chat.id,
                    file_id = get_file_id(msg),
                    file_size = get_file_size(msg)
                )
                cursor.execute(sql)
                conn.commit()
        except Exception as e:
            logging.error(e)
            logging.error(sql)