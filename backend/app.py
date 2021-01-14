from tornado import web, ioloop, httpserver

from backend.app.handler.base_handler import make_app
from backend import settings
from backend.app.model.base_entity_model import init_store
from backend.conf import DEVELOP_MODE
from backend.app.handler import api_route

is_production = bool(not DEVELOP_MODE)

app_settings = {
    "debug": True,
    "cookie_secret": settings.COOKIE_SECRET,
}


def init():
    init_store()


def start_server():
    init_store()
    app = make_app(route_modules=api_route, settings=app_settings)

    server = httpserver.HTTPServer(app, xheaders=True)
    server.listen(settings.PORT, settings.HOST)
    loop = ioloop.IOLoop.current()
    print("is_production:", is_production)
    loop.start()


if __name__ == '__main__':
    start_server()
