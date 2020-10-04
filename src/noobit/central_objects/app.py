import pathlib
import asyncio
import typing
import logging

import httpx
import uvicorn
import fastapi

from noobit.central_objects.api import API
from noobit.central_objects.config import Config
from noobit.central_objects.asgi_app import AsgiApp


# Alex Martelli's 'Borg': http://www.aleax.it/Python/5ep.html
class Borg:
    _shared_state = {}
    _exists = False
    def __init__(self):
        if not self._exists:
            self.__dict__ = self._shared_state
            self._exists = True
        else:
            raise AttributeError("Another instance of this Borg already exists, skip initialisation")

class BorgMeta(type):

    __slots__ = ()

    def __new__(cls, clsname, bases, clsdict):
        """when class is constructed"""
        if not clsdict.get("__slots__", False):
            raise AttributeError("Please define __slots__ for class : ", clsname)

        if isinstance(cls.__slots__, tuple):
            cls.__slots__ += ("_exists", "_persist_args", "_persist_kwargs", "_borg",)
        if isinstance(cls.__slots__, list):
            cls.__slots__.extend(["exists", "_persist_args", "_persist_kwargs"])

        clsdict["_exists"] = False
        return super().__new__(cls, clsname, bases, clsdict)


    def __call__(cls, *args, **kwargs):
        """when instance of class is created"""
        if not cls._exists:
            cls._borg = super().__call__(*args, **kwargs)
            cls._exists = True
            cls._persist_args = args
            cls._persist_kwargs = kwargs
        else:
            print("Instance of Borg already exists, refering to initial Borg")

        return cls._borg



class App(metaclass=BorgMeta):

    # version: str

    # config: Config
    # default_config: dict

    # logger = None

    # app_root_path: pathlib.Path             # should this be in config ?
    # user_folder_path: pathlib.Path          # should this be in config ?

    # srcpath = pathlib.Path("/home/maximemansour2212/python/fastapi/tutorial/noobit/backend/src")
    # api: API = API(srcpath)

    # loop: asyncio.BaseEventLoop = None

    # session: httpx.AsyncClient = None

    # asgi_server: uvicorn.Server = None
    # asgi_config: uvicorn.Config = None
    # asgi_app: fastapi.FastAPI() = AsgiApp()
    __slots__ = (
        "version",
        "logger",
        "config",
        "default_config",
        "app_src_path",
        "loop",
        "session",
        "api",
        "asgi_server",
        "asgi_config",
        "asgi_app",
    )


    def __init__(
            self,
            *,
            version: str = None,
            logger: logging.Logger = None,
            config: dict = None,
            default_config: dict = None,
            app_src_path: pathlib.Path = None,
            loop: asyncio.BaseEventLoop = None,
            session: httpx.AsyncClient = None,
            api: API = None,
            asgi_server: uvicorn.Server = None,
            asgi_config: uvicorn.Config = None,
            asgi_app: fastapi.FastAPI = None,
        ):
        super().__init__()
        self.version = version
        self.logger = logger
        self.config = config
        self.default_config = default_config
        self.app_src_path = app_src_path if app_src_path else None # replace later with : config["APP_SRC_PATH"]    # we do want to raise an error in case there is no path in config file
        self.loop = loop if loop else asyncio.get_event_loop()
        self.session = session if session else httpx.AsyncClient()      # apparently we can pass an <auth> param to sessions ==> could this be used to pass <Exchange>Auth class ?
        self.api = api if api else API(app_src_path)
        self.asgi_server = asgi_server if asgi_server else None
        self.asgi_config = asgi_config if asgi_config else None
        self.asgi_app = asgi_app if asgi_app else AsgiApp()

        # setup children
        self._register_children()
        self.api._forward_app()
        self.api.rest._register_exchanges(self.app_src_path)

        self._register_app()
        # print("Initialising : ", self)

    def _register_children(self):
        print("registering App children")
        self.api._register_parent(self)
        self.api.rest._register_tree()

    def _register_app(self):
        """Bind app to children objects"""
        self.asgi_app._register_app(self)




if __name__ == "__main__":

    app = App(
    app_src_path=pathlib.Path("/home/maximemansour2212/python/fastapi/tutorial/noobit/backend/src")
    )

    app2 = App()
    print("<<<< App2 app_src_path : ", app2.app_src_path)

    print("===> app.api.rest.kraken : ", app.api.rest.kraken)
    print("===> Available Exchanges : ", app.api.rest.available_exchanges)
    print("===> APIs parent : ", app.api.parent)
    print("===> RestAPIs parent : ", app.api.rest.parent)
    print("===> Parents tree : ", app.api.rest.tree)
    print("===> Kraken RestAPI app attr : ", app.api.rest.kraken.app)
    print("===> Kraken RestAPI tree : ", app.api.rest.tree)
    print("===> ASGI App Object / bound app : ", app.asgi_app, app.asgi_app.app)
    print("===> Get Instrument : ", asyncio.run(app.api.rest.kraken.get_instrument("XBT-USD")))
