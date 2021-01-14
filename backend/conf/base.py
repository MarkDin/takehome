import os

DEVELOP_MODE = bool(os.environ.get('DEVELOP_MODE') == 'True')

MYSQL_CONF = {
    'db': 'test_fox',
    'port': 3306,
    'host': '127.0.0.1',
    'user': 'root',
    'password': '154310',
}

COOKIE_SECRET = ""
CROSS_SETTINGS = ""
HOST = "127.0.0.1"
PORT = 9999




