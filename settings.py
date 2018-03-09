# coding: utf8

restricted_characters = [
    '<',
    '>',
    '&'
]

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
    'get_notifications': '1',
    'greeting': {
        'is_enabled': '0',
        'text': 'no_notification_f883edc218bff19b8c943fe397cc83895ce169c5',
    },
    'deletions': {
        'url': '0',
        'system': '0',
        'files': {
            'photo': '0',
            'voice': '0',
            'videos': '0',
            'stickers': '0',
            'forwards': '0',
        }
    },
    'warns': '3',
    'kick_bots': '0'
}

default_user_settings = {
    'language': 'no_language_set',
    'get_notifications': '1'
}

settings_statuses = {
    '0': '❌',
    '1': '✅'
}

settings_states = {
    '0': '1',
    '1': '0'
}