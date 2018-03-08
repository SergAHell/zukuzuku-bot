import api
import config
import time
import datetime


got_time = msg.date
solved_time = int(time.time())
delta = datetime.datetime.fromtimestamp(solved_time-got_time).strftime('%H:%M:%S'))


start_time = time.time()
print(type(api.get_chats_count()))
end_time = time.time()
print((end_time-start_time)*1000)

start_time = time.time()
print(type(api.get_chats_countt()))
end_time = time.time()
print((end_time-start_time)*1000)