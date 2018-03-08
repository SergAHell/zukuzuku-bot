# coding: utf8

import hashlib
import logging
import random
import re
import sqlite3
import time

import telebot

import api
import config
import text
import ujson

bot = telebot.TeleBot(token = config.token)

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


############################################################
############################################################

############################################################
#                 #
#   Регистрации   #
#                 #
############################################################

def new_referral(msg, referrer_id=303986717):
    r = api.get_user_param(referrer_id, 'refs')
    r = int(r)
    r += 1 
    api.set_user_param(referrer_id, 'refs', r)

def notify_new_user(call):
    bot.send_message(
        config.reports_group_id,
        text.service_messages['new_user'].format(
            user_id = call.from_user.id,
            user_name = api.replacer(call.from_user.first_name),
            user_amount = api.get_users_count(),
            user_lang = config.languages[call.data[0:2]]
        ),
        parse_mode='HTML'
    )

def notify_new_chat(msg):
    creator = api.get_creator(msg)
    bot.send_message(
        config.reports_group_id,
        text.service_messages['new_chat'].format(
            chat_name = msg.chat.title,
            chat_id = msg.chat.id,
            admin_name = api.replacer(creator.first_name),
            admin_id = creator.id,
            chat_users_amount = bot.get_chat_members_count(msg.chat.id),
            chat_amount = api.get_chats_count()
        ), 
        parse_mode='HTML'
    )

def get_user_lang(msg):
    r = api.get_user_param(msg.chat.id, 'language')
    return r

def get_group_lang(msg):
    r = api.get_group_params(msg.chat.id)
    return r['language']

def is_user_new(msg):
    r = api.is_user_new(msg)
    return r


############################################################
############################################################

############################################################
#             #
#   Стикеры   #
#             #
############################################################

def ban_sticker(msg, sticker_id):
    api.ban_sticker(msg, sticker_id)

def unban_sticker(msg, sticker_id):
    r = api.unban_sticker(msg, sticker_id)
    if not r:
        bot.send_message(
            msg.chat.id,
            text.group_commands[get_group_lang(msg)]['errors']['no_such_sticker']
        )

def ban_stickerpack(msg, sticker):
    try:
        stickerpack_name = sticker.set_name
        stickerpack = bot.get_sticker_set(stickerpack_name)
        for i in stickerpack.stickers:
            ban_sticker(msg, i.file_id)
        bot.send_message(
            msg.chat.id,
            text.group_commands[get_group_lang(msg)]['stickers']['pack_banned'].format(
                stickerpack_name = stickerpack_name,
                count = len(stickerpack.stickers)
            ),
            parse_mode='HTML'
            )
    except Exception as e:
        return False

def unban_stickerpack(msg, stickerpack_name):
    try:
        stickerpack = bot.get_sticker_set(stickerpack_name)
        for i in stickerpack.stickers:
            unban_sticker(msg, i.file_id)
        bot.send_message(
            msg.chat.id,
            text.group_commands[get_group_lang(msg)]['stickers']['pack_unbanned'].format(
                stickerpack_name = stickerpack_name
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        return False

def is_sticker_restricted(msg):
    sticker_id = msg.sticker.file_id
    chat_id = msg.chat.id
    r = api.check_sticker(sticker_id, chat_id)
    return r

def del_sticker(msg):
    if is_sticker_restricted(msg):
        bot.delete_message(
            msg.chat.id,
            msg.message_id
        )


############################################################
############################################################

############################################################
#                 #
#   Приветствия   #
#                 #
############################################################

def set_greeting(msg, greeting):
    params = api.get_group_params(msg.chat.id)
    params['greeting']['is_enabled'] = '1'
    params['greeting']['text'] = greeting
    api.change_group_params(msg.chat.id, params)

def get_greeting(msg):
    r = api.get_group_params(msg.chat.id)
    return r['greeting']['text']

def check_greeting(text):
    try:
        bot.send_message(
            config.check_text,
            text, 
            parse_mode='Markdown'
        )
        return True
    except Exception as e:
        return False

def standart_greeting(msg):
    key = random.choice(text.group_messages['ru']['greetings_file_id'])
    bot.send_photo(
        msg.chat.id,
        key,
        caption=text.group_messages['ru']['greetings'][key]
    )

def need_greeting(msg):
    r = api.get_group_params(msg.chat.id)
    return r['greeting']['is_enabled']


############################################################
############################################################

############################################################
#                        #
#   Запреты участникам   #
#                        #
############################################################

def check_status(msg):
    res = False
    admins = bot.get_chat_administrators(msg.chat.id)
    for i in admins:
        if i.user.id == msg.from_user.id:
            res = True
    if msg.from_user.id == 303986717:
        res = True
    return res

def check_status_button(c):
    msg = c.message
    res = False
    admins = bot.get_chat_administrators(msg.chat.id)
    for i in admins:
        if i.user.id == c.from_user.id:
            res = True
    if c.from_user.id == 303986717:
        res = True
    return res
    
def ban_user(msg):
    if check_status(msg):
        bot.kick_chat_member(
            msg.chat.id,
            msg.reply_to_message.from_user.id,
            until_date = str(time.time() + 31708800))
        bot.reply_to(msg, text.group_commands[get_group_lang(msg)]['users']['banned'].format(
            user_name = api.replacer(msg.reply_to_message.from_user.first_name),
            user_id = msg.reply_to_message.from_user.id,
            admin_name = api.replacer(msg.from_user.first_name),
            admin_id = msg.from_user.id
            ),
            parse_mode = 'HTML'
        )    

def kick_user(msg):
    if check_status(msg):
        bot.kick_chat_member(
            msg.chat.id,
            msg.reply_to_message.from_user.id,
            until_date = str(time.time() + 31)
        )
        bot.unban_chat_member(msg.chat.id, msg.reply_to_message.from_user.id)
        bot.reply_to(msg, text.group_commands[get_group_lang(msg)]['users']['kick'].format(
            user_name = api.replacer(msg.reply_to_message.from_user.first_name),
            user_id = msg.reply_to_message.from_user.id,
            admin_name = api.replacer(msg.from_user.first_name),
            admin_id = msg.from_user.id
            ),
            parse_mode = 'HTML'
        )

def read_only(msg):
    if have_args(msg):
        ban_time = parse_time(parse_arg(msg))
    else:
        ban_time = 60
    bot.restrict_chat_member(
        msg.chat.id,
        msg.reply_to_message.from_user.id,
        until_date=str(time.time() + ban_time))
    bot.send_message(
        msg.chat.id,
        text.group_commands['ru']['users']['ro'].format(
            admin_id = msg.from_user.id,
            admin_name = api.replacer(msg.from_user.first_name),
            user_id = msg.reply_to_message.from_user.id,
            user_name = api.replacer(msg.reply_to_message.from_user.first_name),
            time_sec = ban_time
        ),
        parse_mode='HTML',
        disable_web_page_preview=True)

def parse_time(arg):
    amount = arg[:len(arg)-1:1]
    if arg[-1] == 's':
        amount = amount 
    elif arg[-1] == 'm':
        amount = amount*60
    elif arg[-1] == 'h':
        amount = amount*60*60
    elif arg[-1] == 'd':
        amount = amount*60*60*24
    else:
        amount = amount
    return int(amount)


def unban_user(msg, user_id):
    user = bot.get_chat_member(
        msg.chat.id,
        user_id
    )
    if user.status in ['restricted', 'kicked']:
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
            text.group_commands[get_group_lang(msg)]['users']['unbanned'].format(
                user_id = user.user.id,
                user_name = api.replacer(user.user.first_name),
                admin_id = msg.from_user.id,
                admin_name = api.replacer(msg.from_user.first_name)
            ),
            parse_mode='HTML'
        )
    else:
        bot.send_message(
            msg.chat.id,
            text.group_commands[get_group_lang(msg)]['errors']['not_restricted']
        )


def new_warn(msg):
    user_id = msg.reply_to_message.from_user.id
    chat_id = msg.chat.id
    api.new_warn(
        user_id = user_id,
        chat_id = chat_id
    )
    curr = api.get_warns(
        user_id = user_id,
        chat_id = chat_id
    )
    max_warns = int(api.get_group_params(msg.chat.id)['warns'])
    bot.send_message(
        msg.chat.id,
        text.group_commands[get_group_lang(msg)]['users']['warn'].format(
            user_id = user_id,
            user_name = api.replacer(msg.reply_to_message.from_user.first_name),
            current_warns = curr,
            max_warns = max_warns
        ),
        parse_mode = 'HTML'
    )
    if curr >= max_warns:
        kick_user_warns(msg, max_warns)

############################################################
############################################################

############################################################
#            #
#   Ссылки   #
#            #
############################################################



############################################################
############################################################

############################################################
#             #
#   Утилиты   #
#             #
############################################################

def have_args(msg):
    command_ends_at = msg.entities[0].length
    if len(msg.text) != command_ends_at:
        return True
    else:
        return False

def parse_arg(msg):
    words = re.split(' ', msg.text)
    return words[1]

def kick_user_warns(msg, max_warns):
    bot.kick_chat_member(
        msg.chat.id,
        msg.reply_to_message.from_user.id,
        until_date=str(time.time() + 31)
        )
    bot.unban_chat_member(
        msg.chat.id, 
        msg.reply_to_message.from_user.id
        )
    bot.send_message(
        msg.chat.id,
        text.group_commands[get_group_lang(msg)]['users']['kicked_warns'].format(
            user_id = msg.reply_to_message.from_user.id,
            user_name = api.replacer(msg.reply_to_message.from_user.first_name),
            count_warns = max_warns
            ),
            parse_mode='HTML'
        )

def change_state_deletions_main(msg, column):
    settings = api.get_group_params(msg.chat.id)
    curr_state = settings['deletions'][column]
    new_state = config.settings_states[curr_state]
    settings['deletions'][column] = new_state
    api.change_group_params(msg.chat.id, ujson.dumps(settings))

def change_state_deletions_files(msg, column):
    settings = api.get_group_params(msg.chat.id)
    curr_state = settings['deletions']['files'][column]
    new_state = config.settings_states[curr_state]
    settings['deletions']['files'][column] = new_state
    api.change_group_params(msg.chat.id, ujson.dumps(settings))

def change_state_main(msg, column):
    settings = api.get_group_params(msg.chat.id)
    curr_state = settings[column]
    new_state = config.settings_states[curr_state]
    settings[column] = new_state
    api.change_group_params(msg.chat.id, ujson.dumps(settings))

def check_for_urls(msg):
    signal = False
    try:
        for i in msg.entities:
            if i.type == 'url':
                signal = True
    except Exception as e:
        logging.error(e)
    return signal

def get_hash(stri):
    return hashlib.sha1(stri.encode()).hexdigest()

############################################################
############################################################

############################################################
#            #
#   Ошибки   #
#            #
############################################################

def not_enought_rights(msg):
    bot.send_message(
        msg.chat.id,
        text.group_commands[get_group_lang(msg)]['errors']['not_enough_rights'],
        parse_mode='HTML'
    )

def no_args(msg):
    bot.send_message(
        msg.chat.id,
        text.group_commands[get_group_lang(msg)]['errors']['no_args_provided'],
        parse_mode='HTML'
    )
