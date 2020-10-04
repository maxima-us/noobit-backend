import logging
import importlib
import os
import inspect
from pathlib import Path

from fastapi import FastAPI
import stackprinter
stackprinter.set_excepthook(style="darkbg2")

from noobit import runtime
from noobit.engine.base import BaseStrategy
# from noobit.logger.structlogger import get_logger
import noobit_user

logger = logging.getLogger("uvicorn.error")


user_path = noobit_user.get_abs_path()
strat_dir = os.path.join(user_path, "strategies")
strat_dotted = "noobit_user.strategies"

def load_strats(
        app=FastAPI,
    ):
    '''connect to all websockets listed in our mapping'''


    @app.on_event('startup')
    async def list_all_strats():
        strats = [os.path.splitext(i)[0] for i in os.listdir(strat_dir) if not i.startswith("__")]
        for strat in strats:
            dotted = ".".join([strat_dotted, strat])

            # will store ModuleSpec as value, see: https://www.python.org/dev/peps/pep-0451/
            module = importlib.import_module(dotted)
            for _name, obj in inspect.getmembers(module):
                if "noobit_user" in str(obj) and inspect.isclass(obj):
                    print(obj)
                    runtime.Config.available_strategies[strat] = obj