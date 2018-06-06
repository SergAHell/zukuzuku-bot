# coding: utf8

import datetime
import logging
import random
import re
import ssl
import threading
import time
from threading import Timer

import telebot
from telebot import types

import api
import cherrypy
import config
import settings
import text
import ujson
import utils
from aiohttp import web

WEBHOOK_HOST = '31.202.128.8'
WEBHOOK_PORT = 88  # 443, 80, 88 или 8443 (порт должен быть открыт!)
# На некоторых серверах придется указывать такой же IP, что и выше
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)

start_time = int(time.time())

bot = telebot.TeleBot(token=config.token, threaded=True)

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

app = web.Application()

async def handle(request):
    if request.match_info.get('token') == bot.token:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(status=403)

app.router.add_post('/{token}/', handle)

def create_user_language_keyboard():
    lang_keyboard = types.InlineKeyboardMarkup()
    lang_keyboard.add(types.InlineKeyboardButton(text="Русский", callback_data='ru_lang'))
    lang_keyboard.add(types.InlineKeyboardButton(text="English", callback_data='en_lang'))
    lang_keyboard.add(types.InlineKeyboardButton(text="O'zbek", callback_data='uz_lang'))
    lang_keyboard.add(types.InlineKeyboardButton(text='Українська', callback_data='ukr_lang'))
    return lang_keyboard


def delete_msg(chat_id, message_id):
    bot.delete_message(
        chat_id,
        message_id
    )

def group_setting(chat_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    curr_settings = api.get_group_params(chat_id)
    btn = types.InlineKeyboardButton(text = 'Принимать рассылки{}'.format(config.settings_statuses[curr_settings['get_notifications']]), callback_data = 'get_notifications::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Удалять ссылки{}'.format(config.settings_statuses[curr_settings['deletions']['url']]), callback_data = 'del_url::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Удалять системные сообщения{}'.format(config.settings_statuses[curr_settings['deletions']['system']]), callback_data = 'del_system::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Исключать ботов{}'.format(config.settings_statuses[curr_settings['kick_bots']]), callback_data='kick_bots::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Фильтры', callback_data='deletions_settings::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Ограничения новых пользователей', callback_data = 'new_users_restrictions::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Настройка предупреждений', callback_data = 'warns_settings::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Настройка приветствий', callback_data = 'welcome_settings::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    return keyboard

def welcome_settings_kb(chat_id):
    kb = types.InlineKeyboardMarkup(row_width = 4)
    curr_settings = api.get_group_params(chat_id)
    btn = types.InlineKeyboardButton(text = 'Отправлять приветствие в чат: {}'.format(config.settings_statuses[curr_settings['greeting']['is_enabled']]), callback_data = 'welcome_state::{chat_id}'.format(chat_id = chat_id))
    kb.add(btn)
    btn = types.InlineKeyboardButton(text = 'Задержка перед удалением приветствия: {} сек.'.format(curr_settings['greeting']['delete_timer']), callback_data = 'welcome_get::{chat_id}'.format(chat_id = chat_id))
    kb.add(btn)
    btn1 = types.InlineKeyboardButton(text = '➖10', callback_data = 'welcome_timer_-10::{chat_id}'.format(chat_id = chat_id))
    btn2 = types.InlineKeyboardButton(text = '➖5', callback_data = 'welcome_timer_-5::{chat_id}'.format(chat_id = chat_id))
    btn3 = types.InlineKeyboardButton(text = '➕5', callback_data = 'welcome_timer_+5::{chat_id}'.format(chat_id = chat_id))
    btn4 = types.InlineKeyboardButton(text = '➕10', callback_data = 'welcome_timer_+10::{chat_id}'.format(chat_id = chat_id))
    kb.add(btn1, btn2, btn3, btn4)
    btn = types.InlineKeyboardButton(text = 'Показать приветствие', callback_data = 'welcome_get::{chat_id}'.format(chat_id = chat_id))
    kb.add(btn)
    btn = types.InlineKeyboardButton(text = 'Назад', callback_data='to_main_menu::{chat_id}'.format(chat_id = chat_id))
    kb.add(btn)
    return kb


def new_users_restrictions_kb(chat_id):
    keyboard = types.InlineKeyboardMarkup(row_width = 4)
    curr_settings = api.get_group_params(chat_id)
    btn = types.InlineKeyboardButton(text = 'Автоматический read-only на {} час - {}'.format(curr_settings['restrictions']['for_time'], config.settings_statuses[curr_settings['restrictions']['read_only']]), callback_data = 'read_only::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn1 = types.InlineKeyboardButton(text = '➖2', callback_data = 'time_ro_-2::{chat_id}'.format(chat_id = chat_id))
    btn2 = types.InlineKeyboardButton(text = '➖1', callback_data = 'time_ro_-1::{chat_id}'.format(chat_id = chat_id))
    btn3 = types.InlineKeyboardButton(text = '➕1', callback_data = 'time_ro_+1::{chat_id}'.format(chat_id = chat_id))
    btn4 = types.InlineKeyboardButton(text = '➕2', callback_data = 'time_ro_+2::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn1, btn2, btn3, btn4)
    btn = types.InlineKeyboardButton(text = 'Снятие ограничений разрешено для: {}'.format(config.new_users[curr_settings['restrictions']['admins_only']]), callback_data = 'new_restrictions_admins_only_{state}::{chat_id}'.format(state = config.settings_states[curr_settings['restrictions']['admins_only']], chat_id = chat_id))
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Назад', callback_data='to_main_menu::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    return keyboard

def warns_settings_kb(chat_id):
    keyboard = types.InlineKeyboardMarkup(row_width = 4)
    curr_settings = api.get_group_params(chat_id)
    btn = types.InlineKeyboardButton(text = 'Максимальное количество исключений: {}'.format(curr_settings['warns']['count']), callback_data = 'empty_callback::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn1 = types.InlineKeyboardButton(text = '➖2', callback_data = 'warns_count_-2::{chat_id}'.format(chat_id = chat_id))
    btn2 = types.InlineKeyboardButton(text = '➖1', callback_data = 'warns_count_-1::{chat_id}'.format(chat_id = chat_id))
    btn3 = types.InlineKeyboardButton(text = '➕1', callback_data = 'warns_count_+1::{chat_id}'.format(chat_id = chat_id))
    btn4 = types.InlineKeyboardButton(text = '➕2', callback_data = 'warns_count_+2::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn1, btn2, btn3, btn4)
    btn = types.InlineKeyboardButton(text = 'Действие при максимальном кол-ве варнов: {}'.format(config.warns_states[curr_settings['warns']['action']]), callback_data='empty_callback::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn1 = types.InlineKeyboardButton(text = 'Ничего', callback_data = 'warns_action_0::{chat_id}'.format(chat_id = chat_id))
    btn2 = types.InlineKeyboardButton(text = 'Кик', callback_data = 'warns_action_1::{chat_id}'.format(chat_id = chat_id))
    btn3 = types.InlineKeyboardButton(text = 'Бан', callback_data = 'warns_action_2::{chat_id}'.format(chat_id = chat_id))
    btn4 = types.InlineKeyboardButton(text = 'Read-only на сутки', callback_data = 'warns_action_3::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn1, btn2, btn3, btn4)
    btn = types.InlineKeyboardButton(text = 'Назад', callback_data='to_main_menu::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    return keyboard

def remove_warns_kb(user_id):
    kb = types.InlineKeyboardMarkup(row_width=1)
    btn = types.InlineKeyboardButton(text = 'Удалить предупреждения', callback_data = 'delete_warns::{user_id}'.format(user_id = user_id))
    kb.add(btn)
    return kb

def unban_new_user_kb(msg):
    kb = types.InlineKeyboardMarkup(row_width=1)
    btn = types.InlineKeyboardButton(text = 'Разблокировать', callback_data = 'unban_new_user::{chat_id}::{user_id}'.format(user_id = msg.new_chat_member.id, chat_id = msg.chat.id))
    kb.add(btn)
    return kb

def user_settings_main_menu(msg):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    curr_settings = api.get_user_params(msg.chat.id)
    btn = types.InlineKeyboardButton(text = 'Принимать рассылки{}'.format(config.settings_statuses['get_notifications']), callback_data='get_notifications')
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Выбор языка'.format(config.settings_statuses['get_notifications']), callback_data='open_lang_menu')
    keyboard.add(btn)
    return keyboard

def delete_settings(chat_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    curr_settings = api.get_group_params(chat_id)
    for cont_type in config.available_attachments:
        btn = types.InlineKeyboardButton(text=config.available_attachments_str[cont_type].format(config.settings_statuses[curr_settings['deletions']['files'][cont_type]]), callback_data='delete_{content_type}::{chat_id}'.format(content_type = cont_type, chat_id = chat_id))
        keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Переключить все', callback_data = 'change_all::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Назад', callback_data='to_main_menu::{chat_id}'.format(chat_id = chat_id))
    keyboard.add(btn)
    return keyboard

@bot.channel_post_handler(content_types=['text'], func = lambda msg: msg.chat.id == config.channel_ID)
def bot_broadcast(msg):
    bot.forward_message(config.adminID, msg.chat.id, msg.forward_from_message_id)

@bot.channel_post_handler(content_types = ['text'], func = lambda msg: msg.chat.id != config.channel_ID and msg.chat.type == 'channel')
def bot_leave(msg):
    bot.leave_chat(
        msg.chat.id
    )



@bot.message_handler(commands = ['settings'], func = lambda msg: msg.chat.type == 'supergroup')
def bot_answ(msg):
    start_time = time.time()
    message = msg
    kb = types.InlineKeyboardMarkup()
    
    r = bot.reply_to(
        msg,
        'Настройки отправлены вам в личные сообщения',
    )
    kb.add(types.InlineKeyboardButton(text = 'Удалить', callback_data = 'settings_delete {} {}'.format(msg.message_id, r.message_id)))
    bot.edit_message_reply_markup(
        chat_id = msg.chat.id,
        message_id = r.message_id,
        reply_markup = kb
    )
    bot.send_message(
        msg.from_user.id, 
        '<b>Настройки группы {}</b>'.format(msg.chat.title), 
        reply_markup=group_setting(msg.chat.id),
        parse_mode='HTML'
    )
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['start'], func=lambda msg: msg.chat.type == 'private')
def bot_user_start(msg):
    message = msg
    start_time = time.time()
    if utils.is_user_new(msg):
        if utils.have_args(msg):
            referrer = utils.parse_arg(msg)[1]
        bot.send_message(
            msg.chat.id,
            text.user_messages['start'],
            reply_markup=create_user_language_keyboard()
            )
    else:
        bot.send_message(msg.chat.id, text.user_messages[utils.get_user_lang(msg)]['start'])
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['start'], func=lambda msg: msg.chat.type != 'private')
def bot_group_start(msg):
    start_time = time.time()
    message = msg
    api.register_new_chat(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands = ['get_logs'], func = lambda msg: msg.chat.id == -1001236256304 and utils.check_super_user(msg.from_user.id))
def bot_logs(msg):
    bot.send_document(msg.chat.id, open('logs.txt', 'rb'))

@bot.message_handler(commands=['set_text'], func = lambda msg: msg.chat.type != 'private')
def bot_set_text(msg):
    start_time = time.time()
    message = msg
    if len(msg.text) not in [9, 21]:
        new_greeting = msg.text[len(msg.text):msg.entities[0].length:-1][::-1]
        if utils.check_greeting(new_greeting):
            utils.set_greeting(msg, new_greeting)
            bot.send_message(
                msg.chat.id,
                'Приветствие изменено'
            )
        else:
            bot.send_message(
                msg.chat.id,
                text = 'Данное приветствие не работает'
            )
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['kick'], func=lambda msg: msg.chat.type != 'private')
def bot_kick(msg):
    start_time = time.time()
    utils.kick_user(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands = ['ban', 'ban_me_please'], func = lambda msg: msg.chat.type == 'supergroup')
def bot_ban_me_please(msg):
    start_time = time.time()
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
                    user_name = api.replacer(msg.from_user.first_name),
                    t = t
                ), parse_mode = 'HTML')
            else:
                bot.send_message(
                    msg.chat.id,
                    text.group_messages['ru']['user_is_admin'].format(
                        admin_id = msg.from_user.id,
                        admin_name = api.replacer(msg.from_user.first_name)
                    ),
                    parse_mode='HTML'
                )
        except Exception as e:
            logging.error(e)
    else:
        utils.ban_user(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['language'], func=lambda msg: msg.chat.type == 'private')
def bot_lang(msg):
    start_time = time.time()
    bot.send_message(
        msg.chat.id,
        text.user_messages['start'],
        reply_markup=create_user_language_keyboard()
    )
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['ping'])
def bot_ping(msg):
    start_timee = time.time()
    bot.send_message(
        msg.chat.id,
        text.user_messages['ru']['commands']['ping'].format(
            unix_time = datetime.datetime.time(datetime.datetime.now()),
            working_time = round((time.time()-msg.date), 3),
            uptime_sec = int(time.time()-start_time)
        ),
        reply_to_message_id=msg.message_id,
        parse_mode='HTML'
    )
    utils.new_update(msg, time.time()-start_timee)


@bot.message_handler(content_types=['new_chat_members'])
def bot_users_new(msg):
    api.register_new_chat(msg)
    start_time = time.time()
    message = msg
    api.register_new_chat(msg)
    if api.get_group_params(msg.chat.id)['deletions']['system']:
        bot.delete_message(
            msg.chat.id,
            msg.message_id
        )
    if msg.chat.type == 'channel':
        bot.send_message(
            msg.chat.id,
            text.promotion_message,
            parse_mode='HTML'
            )
        bot.leave_chat(
            msg.chat.id
            )
    if msg.new_chat_member.id == 495038140:
        api.register_new_chat(msg)
        api.change_group_params(msg.chat.id, ujson.dumps(config.default_group_settings))
    else:
        if api.get_group_params(msg.chat.id)['restrictions']['read_only']:
            bot.restrict_chat_member(
                msg.chat.id,
                msg.new_chat_member.id,
                until_date = int(time.time()+api.get_group_params(msg.chat.id)['restrictions']['for_time']*3600)
            )
            r = bot.send_message(
                msg.chat.id,
                text.group_commands['ru']['restricted']['new_user']['read_only'].format(
                    user_id = msg.new_chat_member.id,
                    user_name = api.replacer(msg.new_chat_member.first_name),
                    ban_time = api.get_group_params(msg.chat.id)['restrictions']['for_time']
                ),
                reply_markup = unban_new_user_kb(msg),
                parse_mode = 'HTML'
            )
            t = Timer(api.get_group_params(msg.chat.id)['restrictions']['for_time']*3600, delete_msg, (msg.chat.id, r.message_id))
            t.start()
        if msg.new_chat_member.is_bot and api.get_group_params(msg.chat.id)['kick_bots']:
            bot.kick_chat_member(
                msg.chat.id, 
                msg.new_chat_member.id
            )
            bot.send_message(
                msg.chat.id,
                text.group_commands['ru']['restricted']['bot'],
                parse_mode = 'HTML',
                reply_markup = types.ReplyKeyboardRemove()
            )
        elif utils.check_global_ban(msg):
            bot.kick_chat_member(
                msg.chat.id,
                msg.new_chat_member.id
            )
            bot.send_message(
                msg.chat.id,
                text.group_commands['ru']['restricted']['global_ban'].format(
                    user_id = msg.new_chat_member.id,
                    user_name = msg.new_chat_member.first_name
                ),
                parse_mode = 'HTML'
            )
        else:
            if utils.need_greeting(msg):
                r = bot.send_message(
                    msg.chat.id,
                    utils.generate_welcome_text(msg), 
                    parse_mode='HTML'
                )
                t = Timer(api.get_group_params(msg.chat.id)['greeting']['delete_timer'], delete_msg, (msg.chat.id, r.message_id))
                t.start()
    
    utils.new_update(msg, time.time()-start_time)



@bot.message_handler(content_types=[
    'new_chat_members',
    'left_chat_member', 
    'new_chat_title', 
    'new_chat_photo', 
    'delete_chat_photo', 
    'group_chat_created', 
    'supergroup_chat_created', 
    'channel_chat_created', 
    'migrate_to_chat_id', 
    'migrate_from_chat_id', 
    'pinned_message'
    ])
def bot_check_system(msg):
    start_time = time.time()
    if api.get_group_params(msg.chat.id)['deletions']['system']:
        bot.delete_message(
            msg.chat.id,
            msg.message_id
        )
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['report'])
def bot_report(msg):
    start_time = time.time()
    admins = bot.get_chat_administrators(msg.chat.id)
    for i in admins:
        try:
            bot.send_message(
                i.user.id,
                text.reports_messages['report']['to_admin'].format(
                    group_name = api.replacer(msg.chat.title)
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            pass
    bot.reply_to(
        msg,
        text.reports_messages['report']['to_user'],
        parse_mode = 'HTML'
    )
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands = ['unban'], func = lambda msg: msg.chat.type != 'private')
def bot_user_unban(msg):
    start_time = time.time()
    if utils.check_status(msg) and utils.have_args(msg):
        words = utils.parse_arg(msg)[1]
        user_id = int(words)
        utils.unban_user(msg, user_id)
    elif utils.check_status(msg) and not utils.have_args(msg):
        utils.no_args(msg)
    else:
        utils.not_enought_rights(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands = ['reregister'], func = lambda msg: msg.chat.type == 'supergroup')
def bot_reregister(msg):
    start_time = time.time()
    if utils.check_status(msg):
        api.register_new_chat(msg)
        api.change_group_params(msg.chat.id, ujson.dumps(config.default_group_settings))
    bot.send_message(
        msg.chat.id,
        text.group_messages[utils.get_group_lang]['registration'],
        parse_mode = 'HTML'
    )

@bot.message_handler(commands=['ro'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_users_ro(msg):
    start_time = time.time()
    if utils.check_status(msg):
        utils.read_only(msg)
    else:
        utils.not_enought_rights(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['stickerpack_ban'],func=lambda msg: msg.chat.type == 'supergroup')
def bot_stickerpack_ban(msg):
    start_time = time.time()
    if utils.check_status(msg):
        utils.ban_stickerpack(msg)
    else:
        utils.not_enought_rights(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['stickerpack_unban'], func=lambda msg: msg.chat.type != 'private')
def bot_stickerpack_unban(msg):
    start_time = time.time()
    if utils.check_status(msg) and utils.have_args(msg):
        stickerpack_name = utils.parse_arg(msg)[1]
        utils.unban_stickerpack(msg, stickerpack_name)
    utils.new_update(msg, time.time()-start_time)


@bot.message_handler(commands=['sticker_ban'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_sticker_ban(msg):
    start_time = time.time()
    if utils.check_status(msg):
        sticker_id = msg.reply_to_message.sticker.file_id
        utils.ban_sticker(msg, sticker_id)
    elif not utils.check_status(msg):
        utils.not_enought_rights(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['sticker_unban'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_sticker_unban(msg):
    start_time = time.time()
    if utils.have_args(msg) and utils.check_status(msg):
        sticker_id = utils.parse_arg(msg)[1]
        utils.unban_sticker(msg, sticker_id)
    elif check_status(msg) and not utils.have_args(msg):
        utils.not_enought_rights(msg)
    elif utils.have_args(msg) and not check_status(msg):
        utils.no_args(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['help'])
def bot_help(msg):
    start_time = time.time()
    r = bot.send_message(
        msg.from_user.id,
        text.user_messages[utils.get_user_lang(msg)]['help'],
        parse_mode='HTML'
        )
    t = Timer(15, delete_msg, (msg.chat.id, r.message_id))
    t.start()
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['about'], func=lambda msg: msg.chat.type == 'private')
def bot_about(msg):
    start_time = time.time()
    bot.send_message(
        msg.chat.id,
        text.user_messages[utils.get_user_lang(msg)]['about'],
        parse_mode='Markdown')
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['warn'], func=lambda msg: msg.chat.type != 'private')
def bot_new_warn(msg):
    start_time = time.time()
    if utils.check_status(msg):
        utils.new_warn(msg)
    else:
        utils.not_enought_rights(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['donate'])
def bot_donate(msg):
    start_time = time.time()
    bot.send_message(
        msg.chat.id,
        text.group_commands['ru']['donate'],
        parse_mode = 'HTML'
    )
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands = ['get_id'])
def bot_get_id(msg):
    bot.send_message(
        msg.chat.id,
        msg.chat.id
    )

@bot.message_handler(commands = ['get_users'], func = lambda msg: msg.chat.type != 'private')
def bot_get_users(msg):
    start_time = time.time()
    chat_obj = utils.get_chat_info(msg.chat.id)
    users_list = api.get_chat_users(msg.chat.id, 50)
    all_users = api.get_chat_users(msg.chat.id, api.get_chat_users_count(msg.chat.id))
    
    summ = 0
    counter = 0
    for i in all_users:
        counter += 1
        if int(i['user_id']) == msg.from_user.id:
            fixer = counter
    for i in users_list:
        summ = summ + int(i['amount'])
    counter = 0
    mes = text.user_messages[utils.get_group_lang(msg)]['commands']['get_users']['title'].format(
        chat_name = chat_obj.title,
    )
    for i in users_list:
        counter += 1
        mes = mes + text.user_messages[utils.get_group_lang(msg)]['commands']['get_users']['body_nofity'].format(
            user_number = counter,
            user_id = i['user_id'],
            user_name = api.replacer(i['user_name']),
            user_count = i['amount'],
            percent = round(int(i['amount'])/summ*100, 2)
        )    
    mes = mes + text.user_messages[utils.get_group_lang(msg)]['commands']['get_users']['end'].format(
        users_count = api.get_chat_users_count(msg.chat.id),
        messages_count = summ,
        used_time = round((time.time()-start_time), 3),
        user_place = fixer
    )
    try:
        bot.send_message(
            msg.from_user.id,
            mes,
            parse_mode = 'HTML'   
        )
        bot.reply_to(
            msg,
            text.user_messages[utils.get_group_lang(msg)]['commands']['get_users']['chat_response']['success']
        )
    except Exception:
        bot.send_message(
            msg.chat.id,
            text.user_messages[utils.get_group_lang(msg)]['commands']['get_users']['chat_response']['fault']
        )
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands = ['get_all'], func = lambda msg: msg.chat.type != 'private')
def bot_username_all(msg):
    start_time = time.time()
    try:
        bot.send_message(
            msg.from_user.id,
            mes,
            parse_mode = 'HTML'   
        )
        bot.reply_to(
            msg,
            text.user_messages[utils.get_group_lang(msg)]['commands']['get_users']['chat_response']['success']
        )
    except Exception:
        bot.send_message(
            msg.chat.id,
            text.user_messages[utils.get_group_lang(msg)]['commands']['get_users']['chat_response']['fault']
        )
    

@bot.message_handler(commands = ['reset_settings'], func = lambda msg: msg.chat.type != 'private')
def bot_reset_settings(msg):
    start_time = time.time()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text = 'Да, выполнить сброс', callback_data = 'reset_settings_confirmation::{chat_id}'.format(chat_id = msg.chat.id)))
    kb.add(types.InlineKeyboardButton(text = 'Нет, не стоит', callback_data = 'reset_settings_abort::{chat_id}'.format(chat_id = msg.chat.id)))
    if utils.check_status(msg):
        bot.send_message(
            msg.chat.id,
            'Вы действительно хотите сбросить настройки?',
            reply_markup = kb
        )
        

@bot.message_handler(content_types=['text'], func = lambda msg: msg.chat.type == 'supergroup')
def bot_check_text(msg):
    start_time = time.time()
    msg_text = msg.text
    msg_text_low = msg_text.lower()
    if utils.is_restricted(msg) and not utils.check_status(msg):
        bot.delete_message(
            msg.chat.id,
            msg.message_id
        )
        if msg_text_low.startswith('разбан'):
            if utils.check_super_user(msg.from_user.id):
                utils.global_unban(msg)
        elif msg_text.lower() in ['глобал бан']:
                if utils.check_super_user(msg.from_user.id):
                    utils.global_ban(msg)
        elif not utils.check_status(msg):
            # if utils.is_new_in_chat(msg) and api.get_group_params(msg.chat.id)['restrict_new'] == '1':
            if utils.check_for_urls(msg) and api.get_group_params(msg.chat.id)['deletions']['url']:
                    bot.delete_message(
                        msg.chat.id,
                        msg.message_id
                    )
                    bot.send_message(
                        msg.chat.id,
                        text.group_commands[utils.get_group_lang(msg)]['restricted']['url'].format(
                            user_id = msg.from_user.id,
                            user_name = api.replacer(msg.from_user.first_name)
                        ),
                        parse_mode='HTML'
                    )
                # elif utils.check_for_forward(msg) and api.get_group_params(msg.chat.id)['deletions']['forward']:
                #     bot.delete_message(
                #         msg.chat.id,
                #         msg.message_id
                #     )
                #     bot.send_message(
                #         msg.chat.id,
                #         text.group_commands[utils.get_group_lang(msg)]['restricted']['url'].format(
                #             user_id = msg.from_user.id,
                #             user_name = api.replacer(msg.from_user.first_name)
                #         ),
                #         parse_mode='HTML'
                #     )
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(content_types=['photo'], func = lambda msg: msg.chat.id == 303986717)
def bot_text(msg):
    start_time = time.time()
    bot.reply_to(msg, "<code>'{}': '{}',</code>".format(msg.photo[0].file_id, msg.caption), parse_mode ='HTML')
    utils.new_update(msg, time.time()-start_time)


@bot.message_handler(content_types = ['audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'location', 'contact'], func = lambda msg: msg.chat.type == 'supergroup')
def testt(msg):
    start_time = time.time()
    print(utils.is_restricted(msg))
    if utils.is_restricted(msg) and not utils.check_status(msg):
        bot.delete_message(
            msg.chat.id,
            msg.message_id
        )
    utils.new_update(msg, time.time()-start_time)

# Кнопки

@bot.callback_query_handler(func=lambda c: c.data.endswith('lang'))
def change_language(call):
    words = re.split('_', call.data)
    lang = words[0]
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text.user_messages[lang]['chosen_language'])
    api.register_new_user(call, lang)
    utils.new_referral(call.message, referer)

@bot.callback_query_handler(func = lambda c: c.data.startswith('get_notifications'))
def notify_change(c):
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        utils.change_state_main(chat_id, 'get_notifications')
        bot.edit_message_reply_markup(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=group_setting(utils.parse_chat_id(c))
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)[c.data.split('::')[0]]])
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'Вы не являетесь администратором. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)[c.data.split('::')[0]]])
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('del_url'))
def del_url(c):
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        utils.change_state_deletions_main(chat_id, 'url')
        bot.edit_message_reply_markup(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=group_setting(utils.parse_chat_id(c))
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)['deletions']['url']])
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'Вы не являетесь администратором. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)['deletions']['url']])
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('del_system'))
def del_system(c):
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        utils.change_state_deletions_main(chat_id, 'system')
        bot.edit_message_reply_markup(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=group_setting(utils.parse_chat_id(c))
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)['deletions']['system']])
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'Вы не являетесь администратором. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)['deletions']['system']])
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('kick_bots'))
def kick_bots(c):
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        utils.change_state_main(chat_id, 'kick_bots')
        bot.edit_message_reply_markup(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=group_setting(utils.parse_chat_id(c))
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)[c.data.split('::')[0]]])
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)[c.data.split('::')[0]]])
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('deletions_settings'))
def to_deletions(c):
    chat_id = utils.parse_chat_id(c)
    bot.edit_message_reply_markup(
        chat_id = c.message.chat.id,
        message_id = c.message.message_id,
        reply_markup = delete_settings(utils.parse_chat_id(c))
    )
    bot.answer_callback_query(
        callback_query_id = c.id,
        text = 'Переход выполнен.'
    )

@bot.callback_query_handler(func = lambda c: c.data.startswith('delete_'))
def group_settings_deletions(c):
    chat_id = utils.parse_chat_id(c)
    cont_type = re.split('_', c.data)[1].split('::')[0]
    if utils.check_status_button(c):
        if c.data == 'delete_video_note':
            utils.change_state_deletions_files(chat_id, 'video_note')
        else:
            utils.change_state_deletions_files(chat_id, cont_type)
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = delete_settings(utils.parse_chat_id(c))
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены. Статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)['deletions']['files'][cont_type]])
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)['deletions']['files'][cont_type]])
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('change_all'))
def group_settings_deletions_all(c):
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        for i in config.available_attachments:
            utils.change_state_deletions_files(chat_id, i)
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = delete_settings(chat_id)
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены.'
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия.'
        )
@bot.callback_query_handler(func = lambda c: c.data.startswith('to_main_menu'))
def group_settings_deletions_photo(c):
    chat_id = utils.parse_chat_id(c)
    bot.edit_message_reply_markup(
        chat_id = c.message.chat.id,
        message_id = c.message.message_id,
        reply_markup=group_setting(utils.parse_chat_id(c))
    )
    bot.answer_callback_query(
        callback_query_id = c.id,
        text = 'Изменения подтверждены.'
    )

@bot.callback_query_handler(func = lambda c: c.data.startswith('warns_del'))
def del_warns(c):
    user_id = utils.parse_user_id(c)
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        api.zeroing_warns(user_id, chat_id)
        bot.edit_message_text(
            text = 'Предупреждения обнулены.',
            chat_id = chat_id,
            message_id = c.message.message_id
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия.'
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('new_users_restrictions'))
def new_users_restrictions(c):
    chat_id = utils.parse_chat_id(c)
    bot.edit_message_reply_markup(
        chat_id = c.message.chat.id,
        message_id = c.message.message_id,
        reply_markup = new_users_restrictions_kb(chat_id)
    )

@bot.callback_query_handler(func = lambda c: c.data.startswith('read_only'))
def new_users_ro(c):
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        settings = api.get_group_params(chat_id)
        settings['restrictions']['read_only'] = config.settings_states[settings['restrictions']['read_only']]
        api.change_group_params(chat_id, ujson.dumps(settings))
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = new_users_restrictions_kb(chat_id)
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены.'
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия.'
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('time_ro_'))
def ro_time_change(c):
    change_time = int(c.data.split('_')[2].split('::')[0])
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        settings = api.get_group_params(chat_id)
        settings['restrictions']['for_time'] = settings['restrictions']['for_time'] + change_time
        if settings['restrictions']['for_time'] < 1:
            settings['restrictions']['for_time'] = 1
        api.change_group_params(chat_id, ujson.dumps(settings))
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = new_users_restrictions_kb(chat_id)
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены.'
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия.'
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('warns_count_'))
def ro_time_change(c):
    change_count = int(c.data.split('_')[2].split('::')[0])
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        settings = api.get_group_params(chat_id)
        settings['warns']['count'] = settings['warns']['count'] + change_count
        if settings['warns']['count'] < 1:
            settings['warns']['count'] = 1
        api.change_group_params(chat_id, ujson.dumps(settings))
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = warns_settings_kb(chat_id)
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены.'
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия.'
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('warns_settings'))
def warns_count_change(c):
    chat_id = utils.parse_chat_id(c)
    bot.edit_message_reply_markup(
        chat_id = c.message.chat.id,
        message_id = c.message.message_id,
        reply_markup = warns_settings_kb(chat_id)
    )
    bot.answer_callback_query(
        callback_query_id = c.id,
        text = 'Изменения подтверждены.'
    )

@bot.callback_query_handler(func = lambda c: c.data.startswith('warns_action_'))
def warns_count_change(c):
    new_mod = int(c.data.split('_')[2].split('::')[0])
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        settings = api.get_group_params(chat_id)
        settings['warns']['action'] = new_mod
        api.change_group_params(chat_id, ujson.dumps(settings))
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = warns_settings_kb(chat_id)
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены.'
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия.'
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('unban_new_user'))
def unban_new_user(c):
    chat_id = utils.parse_chat_id(c)
    user_id = utils.parse_user_id(c)
    if api.get_group_params(chat_id)['restrictions']['admins_only']:
        if utils.check_status_button(c):
            utils.unban_user_button(c)
            user = bot.get_chat_member(
                chat_id,
                user_id
            )
            bot.edit_message_text(
                text = text.group_commands[utils.get_group_lang(c.message)]['restricted']['new_user']['button_pressed'].format(
                    user_id = user.user.id,
                    user_name = api.replacer(user.user.first_name)
                ),
                parse_mode = 'HTML',
                chat_id = c.message.chat.id,
                message_id = c.message.message_id
            )
            t = Timer(api.get_group_params(chat_id)['greeting']['delete_timer'], delete_msg, (chat_id, c.message.message_id))
            t.start()
        else:
            bot.answer_callback_query(
                callback_query_id = c.id,
                show_alert = True,
                text = 'У вас недостаточно прав для выполнения этого действия.'
            )
    else:
        if c.from_user.id == user_id or utils.check_status_button(c):
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
                bot.edit_message_text(
                    text = text.group_commands[utils.get_group_lang(c.message)]['restricted']['new_user']['button_pressed'].format(
                        user_id = user.user.id,
                        user_name = api.replacer(user.user.first_name)
                    ),
                    parse_mode = 'HTML',
                    chat_id = c.message.chat.id,
                    message_id = c.message.message_id
                )
                t = Timer(api.get_group_params(chat_id)['greeting']['delete_timer'], delete_msg, (chat_id, c.message.message_id))
                t.start()
        else:
            bot.answer_callback_query(
                callback_query_id = c.id,
                show_alert = True,
                text = 'У вас недостаточно прав для выполнения этого действия.'
            )

@bot.callback_query_handler(func = lambda c: c.data.startswith('new_restrictions_admins_only_'))
def warns_count_change(c):
    chat_id = utils.parse_chat_id(c)
    state = c.data.split('_')[4].split('::')[0]
    if utils.check_status_button(c):
        settings = api.get_group_params(chat_id)
        settings['restrictions']['admins_only'] = utils.to_bool(state)
        api.change_group_params(chat_id, ujson.dumps(settings))
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = new_users_restrictions_kb(chat_id)
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены.'
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия.'
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('welcome_settings'))
def welcome_settings(c):
    chat_id = utils.parse_chat_id(c)    
    bot.edit_message_reply_markup(
        chat_id = c.message.chat.id,
        message_id = c.message.message_id,
        reply_markup = welcome_settings_kb(chat_id)
    )
    bot.answer_callback_query(
        callback_query_id = c.id,
        text = 'Изменения подтверждены.'
    )

@bot.callback_query_handler(func = lambda c: c.data.startswith('welcome_state'))
def welcome_settings_state(c):
    chat_id = utils.parse_chat_id(c)    
    if utils.check_status_button(c):
        settings = api.get_group_params(chat_id)
        curr_state = settings['greeting']['is_enabled']
        new_state = config.settings_states[curr_state]
        settings['greeting']['is_enabled'] = new_state
        api.change_group_params(chat_id, ujson.dumps(settings))
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = welcome_settings_kb(chat_id)
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены.'
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия.'
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('welcome_timer'))
def welcome_timer_change(c):
    change_count = int(c.data.split('_')[2].split('::')[0])
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        settings = api.get_group_params(chat_id)
        settings['greeting']['delete_timer'] = settings['greeting']['delete_timer'] + change_count
        if settings['greeting']['delete_timer'] < 0:
            settings['greeting']['delete_timer'] = 0
        api.change_group_params(chat_id, ujson.dumps(settings))
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = welcome_settings_kb(chat_id)
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены.'
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия.'
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('settings_delete'))
def del_settings(c):
    words = c.data.split()
    bot.delete_message(
        c.message.chat.id,
        words[1]
    )
    bot.delete_message(
        c.message.chat.id,
        words[2]
    )

@bot.callback_query_handler(func = lambda c: c.data.startswith('welcome_get'))
def get_welcome_text(c):
    chat_id = utils.parse_chat_id(c)
    bot.send_message(
        c.message.chat.id,
        utils.get_greeting(chat_id),
        parse_mode = 'HTML'
    )

@bot.callback_query_handler(func = lambda c: c.data.startswith('reset_settings'))
def reset_settings_button(c):
    chat_id = utils.parse_chat_id(c)
    if utils.check_status_button(c):
        if c.data.startswith('reset_settings_confirmation'):
            api.change_group_params(chat_id, ujson.dumps(config.default_group_settings))
            bot.send_message(
                c.message.chat.id,
                'Настройки сброшены.'
            )
            bot.delete_message(
                c.message.chat.id,
                c.message.message_id
            )
        else:
            bot.delete_message(
                c.message.chat.id,
                c.message.message_id
            )
            bot.send_message(
                c.message.chat.id,
                'Сброс отменен'
            )

# Вебхук

bot.remove_webhook()

bot.set_webhook(
    url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
    certificate=open(WEBHOOK_SSL_CERT, 'r'))

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

# Start aiohttp server
web.run_app(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_PORT,
    ssl_context=context,
)
# bot.remove_webhook()
# bot.polling()
