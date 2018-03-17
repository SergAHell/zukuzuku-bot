# coding: utf8

import utils
import api
import ujson
import config
import time

counter = 0
start_time = int(time.time())
print(start_time)
l = api.get_all()
print(len(l))
for i in l:
    try:
        counter += 1
        curr_settings = api.get_group_params(i['chat_id'])
        curr_settings['deletions']['restrict_new'] = '0'
        curr_settings['deletions']['audio'] = '0'
        curr_settings['deletions']['document'] = '0'
        curr_settings['deletions']['sticker'] = '0'
        curr_settings['deletions']['video'] = '0'
        curr_settings['deletions']['video_note'] = '0'
        curr_settings['deletions']['voice'] = '0'
        curr_settings['deletions']['location'] = '0'
        curr_settings['deletions']['contact'] = '0'
        sql = api.change_group_params(msg.chat.id, curr_settings)
        s = 'Completed chats - {}. Used time - {} secs. Speed - {} chats/second. '
        curr_time = time.time()
        print(s.format(
            counter,
            round(curr_time-start_time, 3),
            round(counter/(curr_time-start_time), 3)
        ))
    except Exception as e:
        print(e)