# -*- coding: utf-8 -*-

import ujson

adminID = 0

reports_group_id = 0
channel_ID = 0
check_text = 0

restricted_characters = [
    '<',
    '>',
    '&'
]

available_languages = [
    'ru',
    'en',
    'uz'
]

available_attachments = [
    'audio',
    'photo',
    'voice',
    'sticker',
    'document',
    'video',
    'video_note',
    'location',
    'contact',
    'text'
]

available_attachments_str = {
    'audio': 'Удалять аудио{}',
    'photo': 'Удалять фотографии{}',
    'voice': 'Удалять аудиосообщения{}',
    'sticker': 'Удалять стикеры{}',
    'document': 'Удалять файлы{}',
    'video': 'Удалять видео{}',
    'video_note': 'Удалять видеосообщения{}',
    'location': 'Удалять геолокации{}',
    'contact': 'Удалять контакты{}',
    'text': 'Удалять текстовые сообщения{}',
}

restricted_characters_replace = {
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;'
}

languages = {
    'ru' : '🇷🇺 Русский',
    'en' : '🇺🇸 English',
    'uz' : "🇺🇿 O'zbek"
}

default_group_settings = {
    'language': 'ru',
    'get_notifications': True,
    'restrict_new': False,
    'greeting': {
        'is_enabled': True,
        'text': 'Добро пожаловать в чат {chat_title}, <a href="tg://user?id={new_user_id}">{new_user_firstname}</a>',
        'delete_timer': 15
    },
    'rules': {
        'is_enabled': True,
        'text': 'Стандартные правила, для смены используйте команду /set_rules',
        'delete_timer': 15
    },
    'deletions': {
        'url': False,
        'system': False,
        'forwards': False,
        'files': {
            'audio': False,
            'photo': False,
            'voice': False,
            'document': False,
            'video': False,
            'video_note': False,
            'location': False,
            'contact': False,
            'text': False,
            'sticker': False
        }
    },
    'restrictions': {
        'read_only': False,
        'for_time': 1,
        'admins_only': True,
    },
    'captcha': {
        'is_on': False,

    },
    'warns': {
        'count': 3,
        'action': 2,
        'for_time': 1
    },
    'kick_bots': False,
    'silent_mode': True,
    'logs_channel': {
        'is_on': False,
        'chat_id': 0
    }
}

warns_states = [
    'Ничего',
    'Кик',
    'Бан',
    'Read-only на сутки'
]

new_users = {
    False: 'новенького',
    True: 'администраторов'
}

default_user_settings = {
    'language': 'no_language_set',
    'get_notifications': True
}

settings_statuses = {
    False: '❌',
    True: '✅'
}

settings_states = {
    False: True,
    True: False
}

available_commands = [
    '/'
]


