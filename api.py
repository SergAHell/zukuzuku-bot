#coding: utf8

import hashlib
import logging
import time

import pymysql
import pymysql.cursors
import requests
import telebot

import config
import secret_config
import settings
import text
import ujson
import utils

bot = telebot.TeleBot(token = secret_config.token)

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
    host = secret_config.host,
    user = secret_config.user,
    password = secret_config.password,
    db = secret_config.db
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
            sql = 'SELECT * FROM `chat_admins` WHERE `admin_id` = %s AND `chat_id` = %s'
            cursor.execute(sql, (i.user.id, chat_id))
            res = cursor.fetchone()
            if res is None:
                sql = 'INSERT INTO `chat_admins` (`chat_id`, `chat_name`, `admin_name`, `admin_id`, `status`) VALUES (%s, %s, %s, %s, %s)'
                cursor.execute(sql, (chat_id, msg.chat.title, i.user.first_name, i.user.id, i.status))
                conn.commit()
        

def ban_sticker(msg, sticker_id):
    """
    Банит стикер\n
    :param msg:\n
    :param sticker_id:\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `banned_stickers` WHERE `chat_id` = %s AND `sticker_id` = %s'
        cursor.execute(sql, (msg.chat.id, sticker_id))
        res = cursor.fetchone()
        if res is None:
            sql = 'INSERT INTO `banned_stickers`(`chat_id`, `chat_name`, `sticker_id`, `ban_time`) VALUES (%s, %s, %s, %s)'
            try:
                cursor.execute(sql, (msg.chat.id, msg.chat.title, sticker_id, int(time.time())))
                conn.commit()
            except Exception as e:
                print(sql)
                print(e)
        else:
            if res != msg.chat.title:
                sql = 'SELECT * FROM `banned_stickers` WHERE `chat_id` = %s'
                cursor.execute(sql, (msg.chat.id, ))
                res = cursor.fetchall()
                for i in res:
                    sql = 'UPDATE `banned_stickers` SET `chat_name` = %s WHERE `chat_id` = %s'
                    cursor.execute(sql, (msg.chat.title, msg.chat.id))
                    conn.commit()

def unban_sticker(msg, sticker_id):
    """
    Разбанивает стикер\n
    :param msg:\n
    :param sticker_id:\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `banned_stickers` WHERE `chat_id` = %s and `sticker_id` = %s'
        cursor.execute(sql, (msg.chat.id, sticker_id))
        res = cursor.fetchone()
        if res is not None:
            sql = 'DELETE FROM `banned_stickers` WHERE `chat_id` = %s and `sticker_id` = %s'
            cursor.execute(sql, (msg.chat.id, sticker_id))
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
        sql = 'SELECT * FROM `users` WHERE `user_id` = %s'
        cursor.execute(sql, (call.from_user.id, ))
        res = cursor.fetchone()
        sec_name = 'None'
        try:
            sec_name = call.from_user.second_name
        except Exception as e:
            sec_name = 'None'
            logging.error(e)
        if res is None:
            sql = 'INSERT INTO `users` (`user_id`, `registration_time`, `first_name`, `second_name`, `language`) VALUES (%s, %s, %s, %s, %s)'
            cursor.execute(sql, (call.from_user.id, int(time.time()), call.from_user.first_name, sec_name, lang))
            conn.commit()
            sql = 'INSERT INTO `user_settings` (`user_id`, `registration_time`, `language`) VALUES (%s, %s, %s)'
            cursor.execute(sql, (call.from_user.id, int(time.time()), lang))
            conn.commit()
            utils.notify_new_user(call)
        else:
            sql = 'UPDATE `user_settings` SET `language` = %s WHERE `user_id` = %s'
            cursor.execute(sql, (lang, call.from_user.id))
            conn.commit()

def register_new_chat(msg):
    """
    Регистрирует новый чат\n
    :param msg:\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM chats WHERE `chat_id` = %s'
        cursor.execute(sql, (msg.chat.id, ))
        res = cursor.fetchone()
        if res is None:
            creator = get_creator(msg)
            sql = 'INSERT INTO `chats` (`chat_id`, `chat_name`, `creator_name`, `creator_id`, `chat_members_count`, `registration_time`, `settings`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
            try:
                cursor.execute(sql, (msg.chat.id, msg.chat.title, creator.first_name, creator.id, bot.get_chat_members_count(msg.chat.id), int(time.time()), ujson.dumps(config.default_group_settings)))
                conn.commit()
            except Exception as e:
                logging.error('error')
                logging.error(sql)
            utils.notify_new_chat(msg)
            register_admins(msg)
        else:
            register_admins(msg)

def get_users_count():
    """
    Возвращает количество пользователей в базе\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT COUNT(`user_id`) FROM `users`'
        cursor.execute(sql)
        res = cursor.fetchall()
        return res['COUNT(`user_id`)']

def get_chats_count():
    """
    Возвращает количество чатов в базе\n
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT COUNT(`chat_id`) FROM `chats`'
        cursor.execute(sql)
        res = cursor.fetchone()
        return res['COUNT(`chat_id`)']

def get_user_param(user_id, column):
    """
    Возвращает определенный параметр пользовательских настроек
    :param msg:
    :param column:
    """
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT `{column}` FROM `user_settings` WHERE `user_id` = %s'.format(
            column = column
        )
        sql = sql
        cursor.execute(sql, (user_id, ))
        res = cursor.fetchone()
        return res[column]

def get_user_params(user_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT `settings` FROM `users` WHERE `user_id` = %s'
        cursor.execute(sql, (user_id, ))
        res = cursor.fetchone()
        return res

def set_user_param(user_id, column, state):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'UPDATE `user_settings` SET `{column}` = %s WHERE `user_id` = %s'.format(
            column = column
        )
        cursor.execute(sql, (state, user_id))
        conn.commit()

def get_group_params(chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `chats` WHERE `chat_id` = %s'
        cursor.execute(sql, (chat_id, ))
        res = cursor.fetchone()
        try:
            ujson.loads(res['settings'])['get_notifications']
            return ujson.loads(res['settings'])
        except Exception as e:
            change_group_params(chat_id, ujson.dumps(config.default_group_settings))
            bot.send_message(
                chat_id,
                text.group_commands['ru']['errors']['db_error']['got_error']
            )
            bot.send_message(   
                chat_id,
                text.group_commands['ru']['errors']['db_error']['finshed']
            )
            return ujson.loads(res['settings'])['get_notifications']


def change_group_params(chat_id, new_params):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'UPDATE `chats` SET `settings` = %s WHERE `chat_id` = %s'
        try:
            cursor.execute(sql, (new_params, chat_id))
            conn.commit()
        except Exception as e:
            print(e)
            print(sql)

def is_user_new(msg):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM users WHERE `user_id` = %s'
        cursor.execute(sql, (msg.from_user.id, ))
        r = cursor.fetchone()
        if r is None:
            res = True
        else:
            res = False
        return res

def check_sticker(sticker_id, chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `banned_stickers` WHERE `sticker_id` = %s AND `chat_id` = %s'
        cursor.execute(sql, (sticker_id, chat_id))
        r = cursor.fetchone()
        if r is None:
            return False
        else:
            return True

def get_warns(user_id, chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `warns` WHERE `user_id` = %s AND `chat_id` = %s'
        cursor.execute(sql, (user_id, chat_id))
        res = cursor.fetchone()
        if res is None:
            sql = 'INSERT INTO `warns`(`user_id`, `chat_id`, `warns`) VALUES (%s, %s, %s)'
            warns = 0
            cursor.execute(sql, (user_id, chat_id, warns))
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
        sql = 'UPDATE `warns` SET `warns` = %s WHERE `user_id` = %s AND `chat_id` = %s'
        cursor.execute(sql, (warns, user_id, chat_id))
        conn.commit()

def get_chats():
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `chats` ORDER BY `registration_time` ASC'
        cursor.execute(sql)
        res = cursor.fetchall()
        return res

def get_all():
    all_chats = []
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `chats` ORDER BY `registration_time` ASC'
        cursor.execute(sql)
        res = cursor.fetchall()
        all_chats.extend(res)
        sql = 'SELECT * FROM `users` ORDER BY `registration_time` ASC'
        cursor.execute(sql)
        res = cursor.fetchall()
        all_chats.extend(res)
        return all_chats

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

def update_stats_bot(count):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'INSERT INTO `stats` (`amount`, `check_time`) VALUES (%s, %s)
        cursor.execute(sql, (count, int(time.time())))
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
        sql = 'SELECT * FROM `global_bans` WHERE `user_id` = %s'
        cursor.execute(sql, (user_id, ))
        res = cursor.fetchone()
        if res is None:
            return False
        else:
            return True

def global_ban(user_id):
    with DataConn(db) as conn:
        if not check_global_ban(user_id):
            cursor = conn.cursor()
            sql = 'INSERT INTO `global_bans` (`user_id`) VALUES  (%s)'
            cursor.execute(sql, (user_id, ))
            conn.commit()

def global_unban(user_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'DELETE FROM `global_bans` WHERE `user_id` = %s'
        cursor.execute(sql, (user_id, ))
        conn.commit()

def new_update(msg, end_time):
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'INSERT INTO `proceeded_updates` (`user_id`, `chat_id`, `msg_time`, `used_time`, `proceeded_at`) VALUES (%s, %s, %s, %s, %s)'
        try:
            cursor.execute(sql, user_id, chat_id, msg.date, end_time*1000, int(time.time()))
            conn.commit()
        except Exception as e:
            logging.error(e)
    try:
        new_content(msg, end_time)
    except Exception as e:
        logging.error(e)
    try:
        update_chat_stats(msg)
    except Exception as e:
        logging.error(e)
    try:
        update_user_stats(msg)
    except Exception as e:
        logging.error(e)

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
            sql = 'UPDATE `most_active_users` SET `user_name` = %s, `amount` = %s WHERE `user_id` = %s AND `chat_id` = %s'
            cursor.execute(sql, (user_name, current_updates, user_id, chat_id))
            sql = 'UPDATE `most_active_users` SET `chat_name` = %s WHERE `chat_id` = %s'
            cursor.execute(sql, (chat_name, chat_id))
            conn.commit()
        

def get_user_messages_count(user_id, chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT `amount` FROM `most_active_users` WHERE `chat_id` = %s AND `user_id` = %s'
        cursor.execute(sql, *chat_id, user_id)
        res = cursor.fetchone()
        return res['amount']

def update_chat_stats(msg):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        current_updates = get_chat_updates_count(msg.chat.id)
        sql = 'SELECT * FROM `most_popular_chats` WHERE `chat_id` = %s'
        cursor.execute(sql, (msg.chat.id, ))
        res = cursor.fetchone()
        if res is None:
            sql = 'INSERT INTO `most_popular_chats` (`updates_count`, `chat_id`, `chat_name`, `last_update`) VALUES (%s, %s, %s, %s)'
            cursor.execute(sql, (current_updates, msg.chat.id, msg.chat.title, msg.date))
            try:
                conn.commit()
            except Exception as e:
                logging.error(e)
                logging.error(sql)
        else:
            sql = 'UPDATE `most_popular_chats` SET `updates_count` = %s, `chat_name` = %s, `last_update` = %s WHERE `chat_id` = %s'
            cursor.execute(sql, (current_updates, msg.chat.title, msg.date, msg.chat.id))
            try:
                conn.commit()
            except Exception as e:
                logging.error(e)
                logging.error(sql)

def get_chat_updates_count(chat_id):    
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT `updates_count` FROM `most_popular_chats` WHERE `chat_id` = %s'
        cursor.execute(sql, (chat_id, ))
        res = cursor.fetchone()
        return int(res['updates_count'])

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
        res = msg.voice.file_idfile_id
    return res


def new_message(msg, end_time):
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'INSERT INTO `proceeded_messages` (`user_id`, `chat_id`, `msg_time`, `used_time`, `proceeded_at`, `content_type`) VALUES (%s, %s, %s, %s, %s, %s)'
        cursor.execute(sql, (user_id, chat_id, msg.date, end_time*1000, int(time.time()), msg.content_type))
        conn.commit()

def new_member(msg):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'INSERT INTO `new_chat_members` (`user_id`, `chat_id`, `joined_chat_at`) VALUES (%s, %s, %s)'
        cursor.execute(sql, (msg.new_chat_member.id, msg.chat.id, msg.date))
        conn.commit()

def new_content(msg, end_time):
    new_message(msg, end_time)
    if msg.content_type == 'new_chat_members':
        new_member(msg)
    elif msg.content_type == 'text':
        try:
            with DataConn(db) as conn:
                cursor = conn.cursor()
                sql = 'INSERT INTO `text` (`user_id`, `chat_id`, `text`, `msg_date`, `message_id`) VALUES (%s, %s, %s, %s, %s)'
                cursor.execute(sql, (msg.from_user.id, msg.chat.id, msg.text, msg.date, msg.message_id))
                conn.commit()
        except Exception as e:
            logging.error(e)
            logging.error(sql)
    else:
        try:
            with DataConn(db) as conn:
                cursor = conn.cursor()
                sql = 'INSERT INTO `{cont_type}` (`user_id`, `chat_id`, `file_id`, `file_size`) VALUES (%s, %s, %s, %s)'.format(
                    cont_type = msg.content_type
                )
                cursor.execute(sql, (msg.from_user.id, msg.chat.id, get_file_id(msg), get_file_size(msg)))
                conn.commit()
        except Exception as e:
            logging.error(e)
            logging.error(sql)

def get_chat_users(chat_id, limit):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `most_active_users` WHERE `chat_id` = %s ORDER BY `amount` DESC LIMIT {limit}'.format(limit = limit)
        cursor.execute(sql, (chat_id, ))
        r = cursor.fetchall()
        return r

def get_chat_users_count(chat_id):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT COUNT(`user_id`) FROM `most_active_users` WHERE `chat_id` = %s ORDER BY `amount` DESC'
        cursor.execute(sql, (chat_id, ))
        r = cursor.fetchone()
        return r['COUNT(`user_id`)']

def new_voteban(chat_id, chat_name, victim_id, victim_name, vote_hash):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'INSERT INTO `votebans`(`vote_hash`, `victim_id`, `victim_name`, `chat_id`, `chat_name`, `votes_count`, `votes_limit`, `started_at`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(sql, (vote_hash, victim_id, victim_name, chat_id, chat_name, 0, utils.get_voteban_limit(chat_id), int(time.time())))
        conn.commit()

def update_voteban(vote_hash):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        curr_votes = get_voteban_votes_count(vote_hash)
        utils.set_voteban_votes_count(vote_hash, curr_votes)
        if utils.get_voteban_limit()

def get_voteban_votes_count(vote_hash):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT COUNT(`vote_id`) FROM `voteban` WHERE `vote_id` = %s'
        cursor.execute(sql, (vote_hash, ))
        r = cursor.fetchone()
        return r['COUNT(`vote_id`)']

def set_voteban_votes_count(vote_hash, votes_count):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'UPDATE `votebans SET `votes_count` = %s WHERE `vote_hash` = %s'
        cursor.execute(sql, (votes_count, vote_hash))
        conn.commit()

def get_voteban_info(vote_hash):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT * FROM `votebans` WHERE `vote_hash` = %s'
        cursor.execute(sql, (vote_hash, ))
        r = cursor.fetchone()
        return r

def set_voteban_info(column, state, vote_hash):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'UPDATE `votebans` SET `{column}` = %s WHERE `vote_hash` = %s'.format(column = column)
        cursor.execute(state, vote_hash)
        conn.commit()
