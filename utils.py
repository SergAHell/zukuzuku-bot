# coding: utf8

import hashlib
import logging
import random
import re
from md5 import md5
import time

import pymysql
import telebot
from telebot import types

import api
import config
import settings
import text
import ujson

bot = telebot.TeleBot(token = secret_config.token)

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
                    format='##%(filename)s [LINE:%(lineno)-3d]# %(levelname)-8s - %(name)-9s [%(asctime)s] - %(message)-50s ',
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

def is_new_in_chat(msg):
    pass
    

def get_group_lang(msg):
    r = api.get_group_params(msg.chat.id)
    return r['language']

def is_user_new(msg):
    r = api.is_user_new(msg)
    return r

def check_super_user(user_id):
    if user_id in [303986717, 207737178]:
        return True
    else:
        return False
        
def update_chat_members(msg):
    user_id = msg.new_chat_member.id
    chat_id = msg.chat.id
    if api.new_user_in_chat(user_id, chat_id):
        #api.update_members(user_id, chat_id)
        pass

def check_global_ban(msg):
    res = False
    if not check_super_user(msg.from_user.id):
        res = api.check_global_ban(msg.new_chat_member.id)
    print(msg.new_chat_member.id)
    return res

def global_ban(msg):
    user_id = msg.reply_to_message.from_user.id
    api.global_ban(user_id)
    bot.kick_chat_member(
        msg.chat.id,
        user_id
    )
    bot.send_message(
        msg.chat.id,
        text.group_commands['ru']['users']['global_ban'].format(
            user_id = user_id,
            user_name = msg.reply_to_message.from_user.first_name
        ),
        parse_mode='HTML'
    )
    
def global_unban(msg):
    user_id = int(parse_arg(msg))
    usr = bot.get_chat_member(
        msg.chat.id,
        user_id
    )
    user_name = usr.user.first_name
    if not api.check_global_ban(user_id):
        bot.send_message(
            msg.chat.id,
            text.group_commands['ru']['errors']['global_not_banned'],
            parse_mode='HTML'
        )
    else:
        api.global_unban(user_id)
        bot.send_message(
            msg.chat.id,
            text.group_commands['ru']['users']['global_unban'].format(
                user_id = user_id,
                user_name = user_name
            ),
            parse_mode='HTML'
        )
    

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
    params['greeting']['is_enabled'] = True
    params['greeting']['text'] = greeting
    api.change_group_params(msg.chat.id, ujson.dumps(params))

def get_greeting(chat_id):
    r = api.get_group_params(chat_id)
    return r['greeting']['text']

def check_text(text):
    try:
        bot.send_message(
            config.check_text,
            text, 
            parse_mode='HTML'
        )
        return True
    except Exception as e:
        return False

def need_greeting(msg):
    r = api.get_group_params(msg.chat.id)
    return r['greeting']['is_enabled']

def generate_welcome_text(msg):
    example = api.get_group_params(msg.chat.id)['greeting']['text']
    example = example.format(
        new_user_id = msg.new_chat_member.id,
        new_user_firstname = api.replacer(msg.new_chat_member.first_name),
        new_user_username = msg.new_chat_member.username,
        chat_id = msg.chat.id,  
        chat_title = api.replacer(msg.chat.title)
    )
    return example

def generate_rules_text(msg):
    example = api.get_group_params(msg.chat.id)['rules']['text']
    example = example.format(
        new_user_id = msg.new_chat_member.id,
        new_user_firstname = api.replacer(msg.new_chat_member.first_name),
        new_user_username = msg.new_chat_member.username,
        chat_id = msg.chat.id,  
        chat_title = api.replacer(msg.chat.title)
    )
    return example

def set_rules(msg, rules):
    params = api.get_group_params(msg.chat.id)
    params['rules']['is_enabled'] = True
    params['rules']['text'] = rules
    api.change_group_params(msg.chat.id, ujson.dumps(params))


############################################################
############################################################

############################################################
#                        #
#   Запреты участникам   #
#                        #
############################################################

def check_status(msg):
    res = False
    try:
        admins = bot.get_chat_administrators(msg.chat.id)
        for i in admins:
            if i.user.id == msg.from_user.id:
                res = True
        if msg.from_user.id == 303986717:
            res = True
    except Exception as e:
        logging.error(e)
    return res

def check_status_button(c):
    chat_id = parse_chat_id(c)
    user_id = c.from_user.id
    res = False
    admins = bot.get_chat_administrators(chat_id)
    for i in admins:
        if i.user.id == user_id:
            res = True
    if user_id == 303986717:
        res = True
    return res
    
def ban_user(msg):
    if check_status(msg):
        kb = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(text = 'Разбанить', callback_data='unban {user_id} {chat_id}'.format(
            user_id = msg.reply_to_message.from_user.id,
            chat_id = msg.chat.id
            ))
        kb.add(btn)
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
            reply_markup = kb,
            parse_mode = 'HTML'
        )    
    else:
        not_enought_rights(msg)

def kick_user(msg):
    if check_status(msg):
        if msg.reply_to_message:
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
        else:
            usr = bot.get_chat_member(
                msg.chat.id,
                parse_arg(msg)[1]
            )
            bot.kick_chat_member(
                msg.chat.id,
                usr.user.id,
                until_date = str(time.time() + 31)
            )
            bot.unban_chat_member(msg.chat.id, usr.user.id)
            bot.reply_to(msg, text.group_commands[get_group_lang(msg)]['users']['kick'].format(
                user_name = api.replacer(usr.user.first_name),
                user_id = usr.user.id,
                admin_name = api.replacer(msg.from_user.first_name),
                admin_id = msg.from_user.id
                ),
                parse_mode = 'HTML'
            )
    else:
        not_enought_rights(msg)

def read_only(msg):
    if have_args(msg):
        ban_time = parse_time(parse_arg(msg)[1])
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
    amount = int(arg[:len(arg)-1:1])
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

def unban_user_button(c):
    pass
    
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

def unban_user_button(c):
    user_id = parse_user_id(c)
    chat_id = parse_chat_id(c)
    user = bot.get_chat_member(
        chat_id,
        user_id
    )
    if user.status in ['restricted']:
        bot.restrict_chat_member(
            chat_id,
            user_id,
            can_send_media_messages=True,
            can_add_web_page_previews=True,
            can_send_messages=True,
            can_send_other_messages=True
        )
    else:
        bot.send_message(
            chat_id,
            text.group_commands[get_group_lang(c.message)]['errors']['not_restricted'],
            parse_mode = 'HTML'
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
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text = 'Удалить предупреждения', callback_data = 'warns_del::{chat_id}::{user_id}'.format(user_id = user_id, chat_id = chat_id)))
    max_warns = int(api.get_group_params(msg.chat.id)['warns']['count'])
    bot.send_message(
        msg.chat.id,
        text.group_commands[get_group_lang(msg)]['users']['warn'].format(
            user_id = user_id,
            user_name = api.replacer(msg.reply_to_message.from_user.first_name),
            current_warns = curr,
            max_warns = max_warns
        ),
        parse_mode = 'HTML',
        reply_markup = kb
    )
    settings = api.get_group_params(chat_id)['warns']['action']
    if curr >= max_warns:
        if settings == 0:
            pass
        elif settings == 1:
            kick_user_warns(msg, max_warns)
        elif settings == 2:
            ban_user_warns(msg, max_warns)
        elif settings == 3:
            ro_user_warns(msg, max_warns)    
        api.zeroing_warns(user_id, chat_id)
        

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
#   Voteban   #
#             #
############################################################

def new_voteban(msg):
    victim = msg.reply_to.from_user
    chat_id = msg.chat.id
    vote_hash = md5(str(chat_id) + str(victim.id)).hexdigest()
    r = api.new_voteban(chat_id, victim.id, vote_hash)
    return r

def set_voteban_votes_count(vote_hash, votes_count):
    api.set_voteban_info('votes_count', votes_count, vote_hash)

############################################################
############################################################

############################################################
#             #
#   Утилиты   #
#             #
############################################################

def new_update(msg, end_time):
    try:
        api.new_update(msg, end_time)
    except Exception as e:
        logging.error(e)

def to_bool(in_str):
    if in_str == 'True':
        return True
    else:
        return False

def is_restricted(msg):
    chat_id = msg.chat.id
    try:
        return api.get_group_params(chat_id)['deletions']['files'][msg.content_type]
    except Exception as e:
        print(e)
        print(api.get_group_params(chat_id))

def have_args(msg):
    command_ends_at = msg.entities[0].length
    if len(msg.text) != command_ends_at:
        return True
    else:
        return False

def parse_arg(msg):
    words = msg.text.split()
    return words

def parse_chat_id(c):
    return int(c.data.split('::')[1])

def parse_user_id(c):
    return int(c.data.split('::')[2])

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

def ban_user_warns(msg, max_warns):
    bot.kick_chat_member(
        msg.chat.id,
        msg.reply_to_message.from_user.id,
        until_date=str(time.time() + 1)
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

def ro_user_warns(msg, max_warns):
    bot.restrict_chat_member(
        msg.chat.id,
        msg.reply_to_message.from_user.id,
        until_date=str(time.time() + 86400)
        )
    bot.send_message(
        msg.chat.id,
        text.group_commands[get_group_lang(msg)]['users']['ro_warns'].format(
            user_id = msg.reply_to_message.from_user.id,
            user_name = api.replacer(msg.reply_to_message.from_user.first_name),
            count_warns = max_warns
            ),
            parse_mode='HTML'
        )

def change_state_deletions_main(chat_id, column):
    settings = api.get_group_params(chat_id)
    curr_state = settings['deletions'][column]
    new_state = config.settings_states[curr_state]
    settings['deletions'][column] = new_state
    api.change_group_params(chat_id, ujson.dumps(settings))

def change_state_deletions_files(chat_id, column):
    settings = api.get_group_params(chat_id)
    curr_state = settings['deletions']['files'][column]
    new_state = config.settings_states[curr_state]
    settings['deletions']['files'][column] = new_state
    api.change_group_params(chat_id, ujson.dumps(settings))

def change_state_main(chat_id, column):
    settings = api.get_group_params(chat_id)
    curr_state = settings[column]
    new_state = config.settings_states[curr_state]
    settings[column] = new_state
    api.change_group_params(chat_id, ujson.dumps(settings))

def check_for_urls(msg):
    signal = False
    try:
        for i in msg.entities:
            if i.type == 'url':
                signal = True
    except Exception as e:
        logging.error(e)
    return signal

def check_for_mentions(msg):
    signal = False
    signal = False
    try:
        for i in msg.entities:
            if i.type == 'mention':
                signal = True
    except Exception as e:
        logging.error(e)
    return signal

def is_channel_mention(mention):
    try:
        bot.get_chat_members_count(mention)
        return True
    except Exception:
        return False

def get_hash(stri):
    return hashlib.sha1(stri.encode()).hexdigest()

def get_chat_info(chat_id):
    return bot.get_chat(chat_id)

def get_user_info(chat_id, user_id):
    return bot.get_chat_member(chat_id, user_id)

def get_chat_users(chat_id):
    users = api.get_chat_users(chat_id)
    res = []
    for i in users:
        res.append(i['user_id'])
    return res
    
def create_get_all(chat_id):
    chat_obj = utils.get_chat_info(msg.chat.id)
    users_list = api.get_chat_users(msg.chat.id, 400)
    mes = ''
    for i in users_list:
        try:
            a = bot.get_chat_member(msg.chat.id, i['user_id'])
            if a.user.username:
                mes = mes + ' @' + a.user.username
        except Exception:
            pass
    return mes
    
def delete_msg(chat_id, message_id):
    bot.delete_message(
        chat_id,
        message_id
    )
        
def get_voteban_count(c):
    group_id = c.message.chat.id
    vote_id = c.message.data.split('::')[1]

def get_mention(txt, mention_obj):
    return txt[mention_obj.offset:mention_obj.offset+mention_obj.length:]

def balance_buttons(texts):
    kb = types.ReplyKeyboardMarkup(row_width=2)
    for i in range(0, len(texts)-1, 2):
        btn = types.KeyboardButton(text = texts[i][0])
        btn1 = types.KeyboardButton(text = texts[i+1][0])
        kb.add(btn, btn1)
    if len(texts) % 2 == 1:
        kb.add(types.KeyboardButton(text = texts[-1][0]))
    return kb

############################################################
############################################################

############################################################
#            #
#   Ошибки   #
#            #
############################################################

def not_enought_rights(msg):
    r = bot.send_message(
        msg.chat.id,
        text.group_commands[get_group_lang(msg)]['errors']['not_enough_rights'],
        parse_mode='HTML'
    )
    bot.delete_message(
        msg.chat.id,
        msg.message_id
    )
    t = Timer(15, delete_msg, (chat_id, c.message.message_id))
    t.start()

def no_args(msg):
    r = bot.send_message(
        msg.chat.id,
        text.group_commands[get_group_lang(msg)]['errors']['no_args_provided'],
        parse_mode='HTML'
    )
    t = Timer(15, delete_msg, (chat_id, c.message.message_id))
    t.start()

