# coding: utf8

import datetime
import logging
import random
import re

import time

import telebot
from telebot import types

import api
import cherrypy
import config
import settings
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

start_time = int(time.time())

bot = telebot.AsyncTeleBot(token=config.token, threaded=True)

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

def create_user_language_keyboard():
    lang_keyboard = types.InlineKeyboardMarkup()
    lang_keyboard.add(types.InlineKeyboardButton(text="Русский", callback_data='ru_lang'))
    lang_keyboard.add(types.InlineKeyboardButton(text="English", callback_data='en_lang'))
    lang_keyboard.add(types.InlineKeyboardButton(text="O'zbek", callback_data='uz__lang'))
    return lang_keyboard


def group_setting(msg):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    curr_settings = api.get_group_params(msg.chat.id)
    btn = types.InlineKeyboardButton(text = 'Принимать рассылки{}'.format(config.settings_statuses[curr_settings['get_notifications']]), callback_data = 'get_notifications')
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Удалять ссылки{}'.format(config.settings_statuses[curr_settings['deletions']['url']]), callback_data = 'del_url')
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Удалять системные сообщения{}'.format(config.settings_statuses[curr_settings['deletions']['system']]), callback_data = 'del_system')
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Исключать ботов{}'.format(config.settings_statuses[curr_settings['kick_bots']]), callback_data='kick_bots')
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Фильтры', callback_data='deletions_settings')
    keyboard.add(btn)
    return keyboard

def user_settings_main_menu(msg):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    curr_settings = api.get_user_params(msg.chat.id)
    btn = types.InlineKeyboardButton(text = 'Принимать рассылки{}'.format(config.settings_statuses['get_notifications']), callback_data='get_notifications')
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Выбор языка'.format(config.settings_statuses['get_notifications']), callback_data='open_lang_menu')
    keyboard.add(btn)
    return keyboard

def delete_settings(msg):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    curr_settings = api.get_group_params(msg.chat.id)
    for i in config.available_attachments:
        btn = types.InlineKeyboardButton(text=config.available_attachments_str[i].format(config.settings_statuses[curr_settings['deletions']['files'][i]]), callback_data='delete_{}'.format(i))
        keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Переключить все', callback_data = 'change_all')
    keyboard.add(btn)
    btn = types.InlineKeyboardButton(text = 'Назад', callback_data='to_main_menu')
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



@bot.message_handler(commands = ['settings'], func = lambda msg: msg.chat.type == 'supergroup' and utils.check_status(msg))
def bot_answ(msg):
    start_time = time.time()
    message = msg
    bot.send_message(
        msg.chat.id, 
        '<b>Настройки группы</b>', 
        reply_markup=group_setting(msg),
        parse_mode='HTML'
    )
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['start'], func=lambda msg: msg.chat.type == 'private')
def bot_user_start(msg):
    message = msg
    start_time = time.time()
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
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['start'], func=lambda msg: msg.chat.type != 'private')
def bot_group_start(msg):
    start_time = time.time()
    message = msg
    api.register_new_chat(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['set_text'], func = lambda msg: msg.chat.type != 'private')
def bot_set_text(msg):
    start_time = time()
    message = msg
    if len(msg.text) not in [9, 21]:
        new_greeting = msg.text[len(msg.text):msg.entities[0].length:-1][::-1]
        print(new_greeting)
        utils.set_greeting(msg, new_greeting)
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
    start_time = time.time()
    message = msg
    if msg.new_chat_member.id == 495038140:
        api.register_new_chat(msg)
    if msg.chat.type == 'channel':
        bot.send_message(
            msg.chat.id,
            text.promotion_message,
            parse_mode='HTML'
            )
        bot.leave_chat(
            msg.chat.id
            )
    if msg.new_chat_member.id != 495038140:
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
            #utils.update_chat_members()
            r = utils.need_greeting(msg)
            if int(r) == 1:
                textt = utils.get_greeting(msg)
                res = utils.check_greeting(text)
                if res:
                    bot.send_message(
                        msg.chat.id,
                        textt, 
                        parse_mode='Markdown'
                    )
            if int(r) == 2:
                utils.standart_greeting(msg)
    if api.get_group_params(msg.chat.id)['deletions']['system']:
        bot.delete_message(
            msg.chat.id,
            msg.message_id
        )
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
        words = utils.parse_arg(msg)
        user_id = int(words)
        utils.unban_user(msg, user_id)
    if utils.check_status(msg) and not utils.have_args(msg):
        utils.no_args(msg)
    else:
        utils.not_enought_rights(msg)
    utils.new_update(msg, time.time()-start_time)

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
        words = utils.parse_arg(msg)
        stickerpack_name = words[1]
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
        sticker_id = utils.parse_arg(msg)
        utils.unban_sticker(msg, sticker_id)
    elif check_status(msg) and not utils.have_args(msg):
        utils.not_enought_rights(msg)
    elif utils.have_args(msg) and not check_status(msg):
        utils.no_args(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(content_types=['sticker'], func=lambda msg: msg.chat.type == 'supergroup')
def bot_del(msg):
    start_time = time.time()
    if utils.is_restricted(msg):
        utils.del_sticker(msg)
    utils.new_update(msg, time.time()-start_time)

@bot.message_handler(commands=['help'], func=lambda msg: msg.chat.type == 'private')
def bot_help(msg):
    start_time = time.time()
    bot.send_message(
        msg.chat.id,
        text.user_messages[utils.get_user_lang(msg)]['help'],
        parse_mode='HTML')
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
    if utils.is_restricted(msg) and not utils.check_status(msg):
        bot.delete_message(
            msg.chat.id,
            msg.message_id
        )
    utils.new_update(msg, time.time()-start_time)

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
    utils.new_referral(call.message, referer)

@bot.callback_query_handler(func = lambda c: c.data == 'get_notifications')
def notify_change(c):
    if utils.check_status_button(c):
        utils.change_state_main(c.message, 'get_notifications')
        bot.edit_message_reply_markup(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=group_setting(utils.parse_chat_id(c))
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)[c.data]])
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'Вы не являетесь администратором. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)[c.data]])
        )

@bot.callback_query_handler(func = lambda c: c.data == 'del_url')
def del_url(c):
    if utils.check_status_button(c):
        utils.change_state_deletions_main(c.message, 'url')
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

@bot.callback_query_handler(func = lambda c: c.data == 'del_system')
def del_system(c):
    if utils.check_status_button(c):
        utils.change_state_deletions_main(c.message, 'system')
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

@bot.callback_query_handler(func = lambda c: c.data == 'kick_bots')
def kick_bots(c):
    if utils.check_status_button(c):
        utils.change_state_main(c.message, 'kick_bots')
        bot.edit_message_reply_markup(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            reply_markup=group_setting(utils.parse_chat_id(c))
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Изменения подтверждены. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)[c.data]])
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            show_alert = True,
            text = 'У вас недостаточно прав для выполнения этого действия. Текущий статус настройки: {}'.format(config.settings_statuses[api.get_group_params(chat_id)[c.data]])        )

@bot.callback_query_handler(func = lambda c: c.data == 'deletions_settings')
def to_deletions(c):
    if utils.check_status_button(c):
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = delete_settings(c.message)
        )
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Переход выполнен.'
        )
    else:
        bot.answer_callback_query(
            callback_query_id = c.id,
            text = 'Вы не являетесь администратором'
        )

@bot.callback_query_handler(func = lambda c: c.data.startswith('delete_'))
def group_settings_deletions(c):
    cont_type = re.split('_', c.data)[1]
    if utils.check_status_button(c):
        if c.data == 'delete_video_note':
            utils.change_state_deletions_files(c.message, 'video_note')
        else:
            utils.change_state_deletions_files(c.message, cont_type)
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = delete_settings(c.message)
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

@bot.callback_query_handler(func = lambda c: c.data == 'change_all')
def group_settings_deletions_all(c):
    if utils.check_status_button(c):
        for i in config.available_attachments:
            utils.change_state_deletions_files(c.message, i)
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = delete_settings(c.message)
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
@bot.callback_query_handler(func = lambda c: c.data == 'to_main_menu')
def group_settings_deletions_photo(c):
    if utils.check_status_button(c):
        bot.edit_message_reply_markup(
            chat_id = c.message.chat.id,
            message_id = c.message.message_id,
            reply_markup = group_setting(c.message)
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

# bot.remove_webhook()
# bot.polling()