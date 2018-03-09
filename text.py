# coding: utf8

import random

VERSION = '1.3'

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
            'sticker_ban': 'Стикер <b>{sticker_id}</b> заблокирован. Для разблокировки введите команду <code>/unban {sticker_id}</code>',
            'stickerpack_banned': 'Заблокирован стикерпак <b>{stickerpack_name}</b>, содержащий <code>{count}</code> шт. стикеров.\n'
                                  'Для разблокировки попросите администратора ввести команду <code>/stickerpack_unban {stickerpack_name}</code>',
            'stickerpack_unbanned': 'Стикерпак <b>{stickerpack_name}</b> разблокирован.',
            'sticker_unban': 'Стикер <b>{sticker_id}</b> разблокирован.',
            'ro': '<a href="tg://user?id={admin_id}">{admin}</a> попросил <a href="tg://user?id={user_id}">{user} помолчать на {time_sec} сек.</a>',
            'ping': 'Бот функционирует нормально. Серверное время: <code>{unix_time}</code>\n'
                    'Бот отреагировал на сообщение за <code>{working_time}</code> сек.',
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

        'user_is_admin': 'Даже пробовать не буду: <a href = "tg://user?id={admin_id}">{admin_name}</a> - один из администраторов чата',

        

        'greetings_file_id': [
            'AgADAgADZ6kxG1M_GEgG9RyquUvUI2sNMw4ABKAxDeypprsu6vkDAAEC',
            'AgADAgADcKkxG1M_GEjreI6wBOGOEbjyAw4ABBkPSE0s3-GpBTYDAAEC',
            'AgADAgADZqkxG1M_GEhbsCHANCg0I5fxAw4ABJmllyr9HizxiTcDAAEC',
            'AgADAgADZKkxG1M_GEjwXisVZpyDP6EQnA4ABJu3L-OB0-XEeVUBAAEC',
            'AgADAgADYakxG1M_GEh1sx0Zy8UiLYIOnA4ABBDqVhsTK1f3MlwBAAEC',
            'AgADAgADXakxG1M_GEgETQ9kYGr24tP4Mg4ABBFAi_nDhkZAH_cDAAEC',
            'AgADAgADXKkxG1M_GEh5DvCplGu_dAHyAw4ABA6YcPzwdVQn3DADAAEC',
            'AgADAgADAqkxG_p-GEis9A0U9P1IYEMPMw4ABFlO5Bi3IT-7aAABBAABAg'
        ],
        'greetings': {
            'AgADAgADZ6kxG1M_GEgG9RyquUvUI2sNMw4ABKAxDeypprsu6vkDAAEC': 'too too roo',
            'AgADAgADcKkxG1M_GEjreI6wBOGOEbjyAw4ABBkPSE0s3-GpBTYDAAEC': 'Так приятно видеть тебя здесь :3',
            'AgADAgADZqkxG1M_GEhbsCHANCg0I5fxAw4ABJmllyr9HizxiTcDAAEC': 'Не стесняйся, новым людям тут всегда рады)',
            'AgADAgADZKkxG1M_GEjwXisVZpyDP6EQnA4ABJu3L-OB0-XEeVUBAAEC': 'Извини, я сейчай не в настроении, говори быстрее что тебе там нужно',
            'AgADAgADAqkxG_p-GEis9A0U9P1IYEMPMw4ABFlO5Bi3IT-7aAABBAABAg': 'Не частно тут видно новые лица. Я вижу ты новенький да? Если хочешь, могу быстренько проветсти для тебя экскурс',            'AgADAgADY6kxG1M_GEgdWoAgjNiZwBz3Mg4ABEfoLfr4Fi1p5PYDAAEC': 'Добро пожаловать ня! Чем я могу тебе помочь, ня?',
            'AgADAgADYakxG1M_GEh1sx0Zy8UiLYIOnA4ABBDqVhsTK1f3MlwBAAEC': 'О да, семпай. Поешь еще этих вкусных французских булочек и выпей чаю (а мне налей молочка, я так хочу пить)',
            'AgADAgADXakxG1M_GEgETQ9kYGr24tP4Mg4ABBFAi_nDhkZAH_cDAAEC': 'Рада тебя видеть, нам дорог каждый новый участник чата',
            'AgADAgADXKkxG1M_GEh5DvCplGu_dAHyAw4ABA6YcPzwdVQn3DADAAEC': 'Здрайствуй, друг, да да, именно ты. Добро пожаловать. Желаем тебе всего хорошего, но хокаге стану я!!!'
        },
        
        'ban_me_please': 'Ну, <a href="tg://user?id={user_id}">{user_name}</a>, ты сам этого захотел. Ты выиграл {t} мин. рид-онли. Поздравляем✨✨\n'
                         'Для разблокировки попроси любого администратора написать команду <code>/unban {user_id}</code>',
                         
        'not_in_ban': 'Ошибочка вышла: пользователь <a href="tg://user?id={user_id}">{user_name}</a> не заблокирован!',
                      
        'unbanned': 'Пользователь <a href="tg://user?id={user_id}">{user_name}</a> разлобкирован администратором <a href="tg://user?id={admin_id}">{admin_name}</a>'
    },
    'en': {},
    'uz': {}
}

group_commands = {
    'ru': {
        'errors':{
            'not_enough_rights': 'Извините, но я не могу вам помочь в этом: <b>у вас недостаточно прав для совершения этого действия.</b>',
            'no_such_sticker': 'Извините, но я не могу помочь в этом: <b>данный стикер еще не заблокирован.</b>',
            'no_args_provided': 'Извините, но я не могу помочь в этом: <b>не предоставлено ни одного аргумента.</b>',
            'not_restricted': 'Извините, но я не могу помочь в этом: <b>данный пользователь не был ограничен.</b>'
        },

        'stickers': {
            'banned': 'Стикер <b>{sticker_id}</b> заблокирован.\n'
                            'Для разблокировки попросите любого администратора ввести команду <code>/sticker_id {sticker_id}</code>',
            'unbanned': 'Стикер <b>{sticker_id}</b> разаблокирован.',
            'pack_banned': 'Заблокирован стикерпак <b>{stickerpack_name}</b>, содержащий <code>{count}</code> шт. стикеров.\n'
                                'Для разблокировки попросите администратора ввести команду <code>/stickerpack_unban {stickerpack_name}</code>',
            'pack_unbanned': 'Стикерпак <b>{stickerpack_name}</b> разблокирован.',
        },

        'restricted': {
            'url': 'Удалена ссылка от <a href="tg://user?id={user_id}">{user_name}</a>, так как в чате ссылки разрешены только для администрации.',
            'bot': 'Бот исключен, так как в чате запрещены боты. Для того чтобы добавить его, несмотря на это ограчение, необходимо добавлять бота с правами администратора. Подойдут любые права, а сразу после приглашения их можно забрать.'
        },

        'users': {
            'warn': 'Пользователь <a href="tg://user?id={user_id}">{user_name}</a> предупрежден.\n'
                    'Кол-во предупреждений: <b>{current_warns}</b>.\n'
                    'Максимальное количество предупреждений, после которых пользователь исключается из группы: <b>{max_warns}</b>.',
            'kick': 'Пользователь <a href="tg://user?id={user_id}">{user_name}</a> исключен администратором <a href="tg://user?id={admin_id}">{admin_name}</a>.',
            'ro': '<a href="tg://user?id={admin_id}">{admin_name}</a> попросил <a href="tg://user?id={user_id}">{user_name}</a> помолчать на <code>{time_sec}</code> сек.',
            'banned': 'Пользователь <a href="tg://user?id={user_id}">{user_name}</a> заблокирован администратором <a href="tg://user?id={admin_id}">{admin_name}</a>.\n'
                      'Для разблокировки введите команду <code>/unban {user_id}</code>',
            'unbanned': 'Пользователь <a href="tg://user?id={user_id}">{user_name}</a> разблокирован администратором <a href="tg://user?id={admin_id}">{admin_name}</a>.',
            'kicked_warns': 'Пользователь <a href="tg://user?id={user_id}">{user_name}</a> исключен за превышение допустимого числа предупреждений: <b>{count_warns}</b>'
        }
    },
    'en': {},
    'uz': {},
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
                'Всего чатов в базе: <b>{chat_amount}</b> шт.',
    'stats': ''
}

promotion_message = '<b>Лучший бот для администраторов групп - </b>t.me/zukuzukubot'

reports_messages = {
    'report': {
       'to_admin': 'Вас вызвали в группе <b>{group_name}</b>, прошу обратить внимание.'
                   'Отправитель - <a href="tg://user?id={user_id}">{user_name}</a>.',
       'to_user': 'Спасибо, мы обработаем ваше обращение.\n' 
                  '<b>Учтите, что спам данной командой часто влечет за собой наказание со стороны администрации чата.</b>'
    }
}