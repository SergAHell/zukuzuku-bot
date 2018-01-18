# coding: utf8

import telebot
import re
import ujson

@bot.message_handler(content_types = ['sticker'], func = lambda msg: msg.sticker.set_name in restricted_packs)
def bot_del(msg):
    message = msg
    bot.delete_message(msg.chat.id, message.message_id)

@bot.message_handler(content_types = ['text', 'sticker', 'pinned_message', 'photo', 'audio'])
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