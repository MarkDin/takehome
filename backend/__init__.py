from backend.conf.base import DEVELOP_MODE

if DEVELOP_MODE:
    settings = __import__("conf.develop")
else:
    settings = __import__("conf.production")
