#coding: utf8

import config

class DB:
    def __init__(self, host, user, db, password):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.charset = 'utf8mb4'
        self.cursorclass = pymysql.cursors.DictCursor

class DataConn:
    def __init__(self, db_obj):
        self.host = db_obj.host
        self.user = db_obj.user
        self.password = db_obj.password
        self.db = db_obj.db
        self.charset = db_obj.charset
        self.cursorclass = db_obj.cursorclass

    def __enter__(self):
        self.conn = pymysql.connect(
            host = self.host,
            user = self.user,
            password = self.password,
            db = self.db,
            charset = self.charset,
            cursorclass = self.cursorclass
        )
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        if exc_val:
            raise

db = DB(
    host = config.host,
    user = config.user,
    password = config.password,
    db = config.db
)

def set_user_param(msg, column_name, param):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'UPDATE users SET `{column_name}` = "{param}" WHERE `ID_tg` = {id}'.format(
            column_name = column_name,
            param = param,
            id = msg.from_user.id
        )
        print(sql)
        cursor.execute(sql)
        conn.commit()

def get_user_info(msg, column_name):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT `{column}` FROM users WHERE `ID_tg` = {id}'.format(
            column = column_name,
            id = msg.chat.id    
        )
        print(sql)
        cursor.execute(sql)
        res = cursor.fetchone()
    return res[column_name]

def get_group_param(msg, column_name):
    with DataConn(db) as conn:
        cursor = conn.cursor()
        sql = 'SELECT `{column}` FROM chats WHERE `ID_tg` = {id}'.format(
            column = column_name,
            id = msg.chat.id    
        )
        print(sql)
        cursor.execute(sql)
        res = cursor.fetchone()
    return res[column_name]