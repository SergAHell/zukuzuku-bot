# coding: utf8

import requests
import config
import schedule
import api
import time

def get_info(bot_token, method):
    url = 'https://api.telegram.org/bot{bot_token}/{method}'.format(
        bot_token = bot_token,
        method = method
    )
    res = requests.get(url).json()
    status = res['ok']
    if status:
        return res['result']
    else:
        return res

def check():
    try:
        r = get_info(config.token, 'getWebhookInfo')
        api.update_stats_bot(r['pending_update_count'])
    except Exception as e:
        print(e)
        pass

def deleting():
    try:
        api.delete_pending()
    except Exception as e:
        print(e)

schedule.every(5).seconds.do(check)
schedule.every(7).days.do(deleting)

while True:
    schedule.run_pending()
    time.sleep(1)
