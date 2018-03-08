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
        i['settings'] = ujson.dumps(config.default_group_settings)
        api.change_group_params(i['chat_id'], i['settings'])
        s = 'Completed chats - {}. Used time - {} secs. Speed - {} chats/second. '
        curr_time = time.time()
        print(s.format(
            counter,
            round(curr_time-start_time, 3),
            round(counter/(curr_time-start_time), 3)
        ))
    except Exception as e:
        print(e)