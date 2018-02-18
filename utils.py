# coding: utf8

import sqlite3

import telebot

import api
import config
import text


bot = telebot.TeleBot(token = config.token)

def check_status(msg):
    res = False
    admins = bot.get_chat_administrators(msg.chat.id)
    for i in admins:
        if i.user.id == msg.from_user.id:
            res = True
    if msg.from_user.id == 303986717:
        res = True
    return res

def unban_sticker(msg, sticker_id):
    r = api.unban_sticker(msg, sticker_id)
    return r

def ban_sticker(msg, sticker_id):
    api.ban_sticker(msg, sticker_id)

def ban_stickerpack(msg, sticker):
    try:
        stickerpack_name = sticker.set_name
        stickerpack = bot.get_sticker_set(stickerpack_name)
        for i in stickerpack.stickers:
            ban_sticker(msg, i.file_id)
        return len(stickerpack.stickers), stickerpack_name
    except Exception as e:
        return False

def unban_stickerpack(msg, stickerpack_name):
    try:
        stickerpack = bot.get_sticker_set(stickerpack_name)
        for i in stickerpack.stickers:
            unban_sticker(msg, i.file_id)
        return len(stickerpack.stickers), stickerpack_name
    except Exception as e:
        return False

def notify_new_user(call):
    bot.send_message(
        config.reports_group_id,
        text.service_messages['new_user'].format(
            user_id = call.from_user.id,
            user_name = call.from_user.first_name,
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
            admin_name = creator.first_name,
            admin_id = creator.id,
            chat_users_amount = bot.get_chat_members_count(msg.chat.id),
            chat_amount = api.get_chats_count()
        ), 
        parse_mode='HTML'
    )


