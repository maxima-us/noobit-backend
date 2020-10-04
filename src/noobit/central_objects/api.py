import os
import importlib
import pathlib
import typing




class AppBranch(object):
    """Branch that get added to our App objets hierarchy tree"""

    def __init__(self):
        self.app: typing.Callable = None
        self.parent: typing.Callable = None
        self.tree: typing.Dict[int, typing.Callable] = None


    def _register_app(self, app: typing.Callable):
        """Bind app object to self. To be called by parent"""
        self.app = app


    def _register_parent(self, parent: typing.Callable):
        """Bind parent class to self. To be called by parent"""
        self.parent = parent


    def _register_child(self, attribute: str):
        """
        Child must also be subclass of AppBranch

        e.g API calling self.register_child("rest") to set API.rest.parent to self
        """
        if attribute not in self.__dict__:
            error_msg = f"{self} does not have {attribute} attribute"
            raise AttributeError(error_msg)

        attr_obj = getattr(self, attribute)
        if isinstance(attr_obj, AppBranch):
            attr_obj._register_parent(self)
        else:
            error_msg = f"{attr_obj} should subclass {AppBranch}"
            raise TypeError(error_msg)


    def _register_tree(self):
        """
        sthg sthg docstring
        """
        traverse = {}

        current_obj = self
        levels_deep = 1
        while True:
            parent = getattr(current_obj, "parent", None)
            if parent is not None:
                # print("New parent in tree : ", parent)
                traverse[levels_deep] = current_obj
                current_obj = parent
                levels_deep += 1
            else:
                break

        self.tree = traverse


    def setattr_parent(self, name: str, value):
        """Set attribute <name> of Parent to <value>"""
        setattr(self.parent, name, value)


    def getattr_parent(self, name: str, value):
        """Get attribute <name> of Parent"""
        getattr(self.parent, name, value)




class RestAPI(AppBranch):


    def __init__(self):
        super().__init__()
        self.available_exchanges: typing.Set[str] = set()


    def _register_exchanges(self, app_src_path: pathlib.Path):
        """
        Explore app to map all exchanges to their defined Rest APIs.
        To be called by parent (probably) only after app has been registered.
        """
        exchange_folder_path = app_src_path.joinpath("noobit", "exchanges")
        # print(exchange_folder_path)

        dir_contains = os.listdir(exchange_folder_path)

        for item in dir_contains:
            # print("Current Item : ", item)
            if not item.startswith("_") and \
                os.path.isdir(exchange_folder_path.joinpath(item)) and \
                item not in ["base", "mappings"]:   # TODO delete mappings folder
                # print("Folder in directory : ", item)
                exchange = item
                api_module = importlib.import_module(".".join(["noobit.exchanges", exchange, "rest", "api"]))

                # we get back <Exchange>RestAPI class
                exchange_rest_api = getattr(api_module, f"{exchange.title()}RestAPI")

                #FIXME do we actually want to register the app, or the parent (to pass data back from individual APIs to global ??)
                setattr(self, exchange, exchange_rest_api(app=self.app, parent=self))

                self.available_exchanges.add(exchange)




class WsAPI(AppBranch):


    def __init__(self):
        super().__init__()

        self.available_exchanges: typing.Set[str] = set()
        self.available_feedreaders: typing.Dict[str, typing.Dict[str, typing.Any]] = {}


    def _register_exchanges(self, app_src_path: pathlib.Path):
        """
        To be called by parent (probably) only after app has been registered.
        """

        exchange_folder_path = app_src_path.joinpath("noobit", "exchanges")

        dir_contains = os.listdir(exchange_folder_path)

        for item in dir_contains:

            if not item.startswith("_") and \
                os.path.isdir(exchange_folder_path.joinpath(item)) and \
                item not in ["base", "mappings"]:   # TODO delete mappings folder

                exchange = item
                public_module = importlib.import_module(".".join(["noobit.exchanges", exchange, "websockets", "public"]))
                private_module = importlib.import_module(".".join(["noobit.exchanges", exchange, "websockets", "private"]))
                private_feed_reader = getattr(private_module, f"{exchange.title()}PrivateFeedReader")
                public_feed_reader = getattr(public_module, f"{exchange.title()}PublicFeedReader")
                exchange_ws = {"public": public_feed_reader, "private" : private_feed_reader}
                setattr(self, exchange, exchange_ws)
                # print("set : ", exchange, "to : ", exchange_rest_api)
                self.available_exchanges.add(exchange)
                self.available_feedreaders.setdefault(exchange, exchange_ws)




class StratAPI(AppBranch):


    def __init__(self):
        super().__init__()
        self.available_strategies: typing.Set[str] = set()


    def _register_strategies(self, app_src_path: pathlib.Path):
        """
        To be called by parent (probably) only after app has been registered.
        """

        user_strats_folder_path = app_src_path.joinpath("noobit_user", "strategies")
        dir_contains = os.listdir(user_strats_folder_path)

        for item in dir_contains:
            # print("Current Item : ", item)
            if not item.startswith("_") and\
                os.path.isfile(user_strats_folder_path.joinpath(item)):

                # remove ".py" extension
                strat = item.split(".")[0]
                strat_module = importlib.import_module(".".join(["noobit_user", "strategies", strat]))
                strat_obj = getattr(strat_module, "Strategy")
                setattr(self, strat, strat_obj)

                self.available_strategies.add(strat)



class API(AppBranch):

    def __init__(self, app_src_path: pathlib.Path):
        # parent is necessarily app
        self.parent: typing.Callable = None

        self.rest: RestAPI = RestAPI()
        # self.ws: WsAPI = WsAPI(app_src_path)
        # self.strat: StratAPI = StratAPI(app_src_path)

        self._register_child("rest")
        # self._register_child("ws")
        # self._register_child("strat")

        print("Initialising : ", self)


    def _forward_app(self):
        """Forward app object to children object. Needs to be called by app object"""
        print("forward app object to children : ", self.parent)
        self.rest._register_app(self.parent)






if __name__ == "__main__":

    print(os.path.abspath(__file__))

    homepath = pathlib.Path("/home/maximemansour2212/python/fastapi/tutorial/noobit/backend/src")

    api = API(homepath)

    restapi = api.rest
    # stratapi = api.strat
    # wsapi = api.ws

    print("Parent class of RestAPI", api.rest.parent)
    restapi.setattr_parent("errors", "NEW ERROR AHHHHHH")
    print("Error received : ", api.errors)
    kraken = getattr(restapi, "kraken")
    print("kraken app : ", kraken.app)
    print("available exchanges : ", api.rest.available_exchanges)
    # print("available strats : ", api.strat.available_strategies)
    # print("available ws : ", api.ws.available_feedreaders)