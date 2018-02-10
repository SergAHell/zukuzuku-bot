# coding: utf8

import random

VERSION = '1.1'

user_messages = {
    'start': '👋',
    'ru': {
        'chosen_language': 'Привет! Ты выбрал русский язык. Чтобы изменить его в дальнейшем - напиши команду /language. Теперь еще раз напиши /start, чтобы получить доступ к боту',

        'start': 'Привет! Я твой новый помощник в чате! Чтобы использовать весь мой функционал, добавь меня в подконтрольную тебе группу, выдай все права (последний необязателен), а напиши сюда /help',
        
        'help': 'Итак, мои команды написаны ниже: \n'
                '/start - Начинает диалог с ботом\n'
                '/help - Выводит это сообщение\n'
                '/about - Выводит контакты разработчика и дополнительную информацию\n'
                '/language - Сбрасывает выбранный язык и позволяет сменить его\n'
                '/sticker_ban - Банит стикер и удаляет все сообщения, содержащие его, пока один из администраторов его не разбанит. Доступно только администраторам\n'
                '/sticker_unban - Разбанивает стикер и прекращает его удаление. Доступно только администраторам\n'
                '/ro - Запрещает пользователю писать на некоторое время. \n    Поддерживаемые параметры: секунды (s), минуты (m), часы (h) и дни (d). Если команда отправлена без параметров, то автоматически выдается запрет на 1 минуту\n'
                '/ping - Проверяет доступность бота. Работает везде и доступна для всех. Если бот не ответил на нее в течение первых 5 секунд - либо конкретно сейчас обрабатывается множество других сообщений, либо что-то случилось с сервером\n'
                '<a href="http://telegra.ph/Manual-po-ispolzovaniyu-bota-02-03">Мануал по использованию бота</a>',
            
        'about': 'Бот написан с нуля [Forden](tg://user?id=303986717) и поддерживается в одиночку \n'
                 'Отдельная благодарность каналу @Obzorchik за информационное сотрудничество и поддержку',
        'commands': {
            'sticker_ban': '\nOlib tashlash uchun <code>/sticker_unban {0}</code> ni jo‘nating.',
            'sticker_unban': '<b>{}</b> qora ro‘yxatdan olib tashlandi.',
            'ro': '{} {} dan {} sec jim turishini so‘radi',
            'ping': 'Бот функционирует нормально. Текущее UNIX-время: <code>{unix_time}</code>',
            'ban': 'Пользователь <a href="tg://user?id={user_id}">{user}</a> забанен администратором <a href="tg://user?id={admin_id}">{admin}</a>. \nДля разбана используйте команду <code>/unban {user_id}</code>.',
            'unban': 'Пользователь <a href="tg://user?id={user_id}">{user}</a> разбанен администратором <a href="tg://user?id={admin_id}">{admin}</a>',
            'kick': 'Пользователь <a href="tg"//user?id={user_id}>{user}</a> исключен администратором <a href="tg://user?id={admin_id}">{admin}</a>'
        }
    },
    'en': {
        'chosen_language': "Hi! You've chosen English language. To change it, send command /language. Now send me /start again",

        'start': "Hi! I'm your new chat admin.To use all my power, please, add me to group, where you are admin and then text /start there. For help, use commands /help",
        
        'help': 'So, my commands are written below\n'
                '/start - Start dialog with bot\n'
                '/help - Show this message\n'
                "/about - Show developer's contacts\n"
                '/language - Let you change chosen language\n'
                '/sticker_ban - Ban sticker and delete it automatically\n'
                '/sticker_unban - Unban sticker and lets everyone send it\n'
                '/kick - Kick user from group\n'
                '/ban - Ban user forever in group\n'
                '/ro - Restrict user from writing in group and for some time. \nSupports next args: seconds (s), minutes (s), hours (h) and even days (d). If no args are provided, user will be restricted for 1 minute\n'
                '/ping - Check the availability of the bot\n',
                'about':
                'Bot created by [Forden](tg://user?id=303986717) and supported alone.\n'
                'Thanks to @Obzorchick for info support\n'
                'P.S. If you found any mistakes, please, contact [Forden](tg://user?id=303986717)',
    },
    'uz': {
        'chosen_language': "Salom! Siz O‘zbek tilini tanladingiz. Keinchalik tilni o‘zgartirish uchun /language komandasini yuboring. \nEndi botdan foydalanish uchun yana bir bor /start ni bosing.",
        'start': 'Salom, men sizning guruhdagi yangi yordamchingizman. Mendan to‘liq foydalanish uchun o‘zingiz administrator bo‘lgan guruhga qo‘shib,menga ham administratorlik bering. So‘ngra shu yerga /help deb yozing',
        'help': 'Demak,menda bor buyuruqlar ro‘yxati:\n'
                '/start - Bot bilan muloqotni boshlaydi\n'
                '/help - Ushbu habarni jo‘natadi\n'
                '/about - Bot yaratuvchisi bilan aloqa va qo‘shimcha ma‘lumot\n'
                '/sticker_ban - Stikerni banlaydi, va shunday stikerli habarlarni o‘chiradi\n'
                '/ro - Biron bir foydalanuvchini bir qancha vaqt yoza olmaydigan qilib qo‘yadi.\n    Mavjud vaqt o‘lchamlari: sekund(s), minut(m), soat(h), kun(d). Agarda ushbu buyuruq aniq vaqtsiz jo‘natilsa,avtomatik tarzda 1 daqiqaga o‘qiy olmaydigan qilib qo‘yadi.\n'
                '/ping -Botning ish faoliyatini tekshiradi. Agarda bot 5 sekund ichida javob bermasa, ayni payitda juda ko‘p habarlar qayta ishlanyabdi,yoki server bilan bog‘liq muammo.',

        'about': 'Bot 0 dan [Forden](tg://user?id=303986717) tomonidan yaratilgan va yolg‘iz qo‘llab-quvvatlanadi.\n'
                 '@Obzorchik kanaliga hamkorlik va yordam uchun alohida minnatdorchilik bildiraman.',

        'commands': {
            'sticker_ban':'Stiker <b>{0}</b> qora ro‘yxatga qo‘shildi. \nOlib tashlash uchun <code>/sticker_unban {0}</code> ni jo‘nating.',
            'sticker_unban':'<b>{}</b> qora ro‘yxatdan olib tashlandi.',
            'ro':'{} {} dan {} sec jim turishini so‘radi',
            'ping':'Men tirikman! Hozirgi UNIX-vaqt: <b>{}</b> sec.',
        }
    }
}

group_messages = {
    'start': '👋',
    'ru': {
        'start': 'Привет всем в группе! Меня зовут Зуку-Зуку и я ваш новый администратор. '
                 'Я буду помогать администраторам управлять вами и вообще я достаточно полезный и милый :3. '
                 'Напишите мне в личные сообщения /start, чтобы познакомиться поближе',

        'wrong_commands': 'Неверная команда. Проверьте синтаксис в /help (работает только в личных сообщениях',

        'banned_sticker': 'Стикер <b>{sticker_id}</b> заблокирован.\n' 
                          'Чтобы разблокировать его, введите следующую команду:\n'
                          '<code>/sticker_unban {sticker_id}</code>',

        'unbanned_sticker': 'Стикер <b>{sticker_id}</b> разблокирован',

        'greetings': [
            'Привет, {user_name}! Располагайся с комфортом',
            '',
            ''
        ]
    },
    'en': {},
    'uz': {}
}

service_messages = {
    'new_user': 'Зарегистрирован новый пользователь. \n' \
                'Имя: <a href="tg://user?id={user_id}">{user_name}</a>\n' \
                'ID: <code>{user_id}</code>\n' \
                'Всего пользователей в базе: <b>{user_amount}</b>\n'
                'Выбранный язык: <b>{user_lang}</b>',

    'new_chat': 'Зарегистрирован новый чат\n'
                'Название: <b>{chat_name}</b>\n'
                'Создатель: <a href="tg://user?id={admin_id}">{admin_name}</a>\n'
                'ID: <code>{chat_id}</code>\n'
                'Численность группы: <b>{chat_users_amount}</b> чел.\n'
                'Всего чатов в базе: <b>{chat_amount}</b> шт.'
}