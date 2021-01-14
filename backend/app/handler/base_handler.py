import datetime
import json
from decimal import Decimal
from functools import wraps
from inspect import isawaitable

from tornado import web
from tornado.concurrent import Future
from tornado.web import RequestHandler

IMG_TYPES = ["image/jpg", "image/png", "image/jpeg"]


class JsonError(web.HTTPError):

    def __init__(self, status_code, reason=''):
        self.status_code = status_code
        self.reason = reason
        super().__init__(status_code, reason=reason)


class BaseHandler(RequestHandler):
    url_prefix = "/api"

    def get_current_user(self):
        token = self.get_body_argument("token")
        return self.check_token(token)

    def check_token(self, token):
        return True

    def get_int(self, key, default=None):
        num = self.get_argument(key, default)

        try:
            num = int(num)
        except ValueError:
            if not default:
                raise JsonError(400, "参数错误")
            else:
                return default
        return num


class route(object):
    _routes = []

    def __init__(self, uri, name=None):
        self._uri = uri
        self.name = name

    def __call__(self, handler):
        uri = self._uri
        if hasattr(handler, 'url_prefix'):
            uri = "%s%s" % (handler.url_prefix, uri)
        name = self.name or handler.__name__
        self._routes.append(web.url(uri, handler, name=name))
        return handler

    @classmethod
    def get_routes(cls, modules):
        for r in modules:
            __import__(r)
        return cls._routes


class Encoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def json_serialize(func):
    # json序列化装饰器
    @wraps(func)
    async def _(self, *args, **kwargs):
        result = await make_awaitable(func(self, *args, **kwargs))
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        self.write(json.dumps({'code': 200, 'data': result, 'msg': '操作成功'}, cls=Encoder))

    return _


def make_awaitable(obj):
    if isawaitable(obj):
        return obj
    future = Future()
    future.set_result(obj)
    return future


def need_auth(func):
    @wraps(func)
    def _(self, *a, **kw):
        if not self.current_user:
            raise JsonError(401, reason='请登录')
        return func(self, *a, **kw)

    return _


def make_app(route_modules, settings=None):
    handlers = route.get_routes(route_modules)
    settings = settings or {}
    app = web.Application(handlers=handlers, **settings)
    return app
