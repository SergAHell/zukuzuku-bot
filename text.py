# coding: utf8

import json

VERSION = '1.1'

messages = {
    'start': '👋',
    'ru': {
        'chosen_language': 'Привет! Ты выбрал русский язык. Чтобы изменить его в дальнейшем - напиши команду /language. Теперь еще раз напиши /start, чтобы получить доступ к боту',

        'start': 'Привет! Я твой новый помощник в чате! Чтобы использовать весь мой функционал, добавь меня в подконтрольную тебе группу, выдай все права (последний необязателен), а напиши сюда /help',

        'help': 'Итак, мои команды написаны ниже: \n' \
                '/start - Начинает диалог с ботом\n' \
                '/help - Выводит это сообщение\n'
                '/about - Выводит контакты разработчика и дополнительную информацию\n'
                '/sticker_ban - Банит стикер и удаляет все сообщения, содержащие его, пока один из администраторов его не разбанит. Доступно только администраторам\n'
                '/sticker_unban - Разбанивает стикер и прекращает его удаление. Доступно только администраторам\n'
                '/ro - Запрещает пользователю писать на некоторое время. \n    Поддерживаемые параметры: секунды (s), минуты (m), часы (h) и дни (d). Если команда отправлена без параметров, то автоматически выдается запрет на 1 минуту\n'
                '/ping - Проверяет доступность бота. Работает везде и доступна для всех. Если бот не ответил на нее в течение первых 5 секунд - либо конкретно сейчас обрабатывается множество других сообщений, либо что-то случилось с сервером',

        'about': 'Бот написан с нуля [Forden](tg://user?id=303986717) и поддерживается в одиночку \n'
                 'Отдельная благодарность каналу @Obzorchik за информационное сотрудничество и поддержку',

        'commands': {
            'sticker_ban': '\nOlib tashlash uchun <code>/sticker_unban {0}</code> ni jo‘nating.',
            'sticker_unban': '<b>{}</b> qora ro‘yxatdan olib tashlandi.',
            'ro': '{} {} dan {} sec jim turishini so‘radi',
            'ping': 'Бот функционирует нормально. Текущее UNIX-время: {}',            
        }
        
    },
    'en': {
        'chosen_language': "Hi! You've chosen English language. To change it, send command /language. Now send me /start again",

        'start': 'IN PROGRESS',

        'help': 'IN PROGRESS',

        'about': 'IN PROGRESS'
    },
    'uz': {
        'chosen_language': "Salom! Siz O‘zbek tilini tanladingiz. Keinchalik tilni o‘zgartirish uchun /language komandasini yuboring. \nEndi botdan foydalanish uchun yana bir bor /start ni bosing.",

        'start': 'Salom, men sizning guruhdagi yangi yordamchingizman. Mendan to‘liq foydalanish uchun o‘zingiz administrator bo‘lgan guruhga qo‘shib,menga ham administratorlik bering. So‘ngra shu yerga /help deb yozing',

        'help': 'Demak,menda bor buyuruqlar ro‘yxati:\n' \
                '/start - Bot bilan muloqotni boshlaydi\n' \
                '/help - Ushbu habarni jo‘natadi\n' \
                '/about - Bot yaratuvchisi bilan aloqa va qo‘shimcha ma‘lumot\n' \
                '/sticker_ban - Stikerni banlaydi, va shunday stikerli habarlarni o‘chiradi\n' \
                '/ro - Biron bir foydalanuvchini bir qancha vaqt yoza olmaydigan qilib qo‘yadi.\n    Mavjud vaqt o‘lchamlari: sekund(s), minut(m), soat(h), kun(d). Agarda ushbu buyuruq aniq vaqtsiz jo‘natilsa,avtomatik tarzda 1 daqiqaga o‘qiy olmaydigan qilib qo‘yadi.\n' \
                '/ping -Botning ish faoliyatini tekshiradi. Agarda bot 5 sekund ichida javob bermasa, ayni payitda juda ko‘p habarlar qayta ishlanyabdi,yoki server bilan bog‘liq muammo.',

        'about': 'Bot 0 dan [Forden](tg://user?id=303986717) tomonidan yaratilgan va yolg‘iz qo‘llab-quvvatlanadi.\n' \
                 '@Obzorchik kanaliga hamkorlik va yordam uchun alohida minnatdorchilik bildiraman.',

        'commands': {
            'sticker_ban': 'Stiker <b>{0}</b> qora ro‘yxatga qo‘shildi. \nOlib tashlash uchun <code>/sticker_unban {0}</code> ni jo‘nating.',
            'sticker_unban': '<b>{}</b> qora ro‘yxatdan olib tashlandi.',
            'ro': '{} {} dan {} sec jim turishini so‘radi',
            'ping': 'Men tirikman! Hozirgi UNIX-vaqt: <b>{}</b> sec.',            
        }
    }
}
