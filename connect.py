import db_config as cfg
# from cx_Oracle import SessionPool
# con = cx_Oracle.connect(cfg.username, cfg.password, cfg.dsn, encoding=cfg.encoding)


try:
    import cx_Oracle
except ImportError:
    print("Error import cx_Oracle :", cx_Oracle.DataError)


def init_session(connection, requestedTag_ignored):
    cursor = connection.cursor()
    print("Cursor init_session created!")
    cursor.close()


pool_min = 2
pool_max = 4
pool_inc = 1
_pool = cx_Oracle.SessionPool(cfg.username, cfg.password, cfg.dsn,
                              encoding=cfg.encoding, min=pool_min, max=pool_max, increment=pool_inc,
                              threaded=True, sessionCallback=init_session)
print("Пул соединенй БД Oracle создан...")


def get_connection():
    if cfg.Debug:
        print("Получаем курсор!")
    return _pool.acquire()


class UserF(object):
    def __init__(self, id, title, intro, text, date):
        self.id = id
        self.title = title
        self.intro = intro
        self.text = text
        self.date = date


if __name__ == "__main__":
    print("Тестируем CONNECT блок!")
    con = get_connection()
    print("Версия: " + con.version)
    val = "Hello from main"
    con.close()
    _pool.close()

