import logging
import importlib
import os
import inspect
from pathlib import Path

from fastapi import FastAPI
import stackprinter
stackprinter.set_excepthook(style="darkbg2")

from noobit import runtime
# from noobit.logger.structlogger import get_logger
import noobit_user

logger = logging.getLogger("uvicorn.error")


user_path = noobit_user.get_abs_path()
exec_models_dir = os.path.join(user_path, "execution_models")
exec_path_dotted = "noobit_user.execution_models"


def load_exec_models(
        app=FastAPI,
    ):

    @app.on_event('startup')
    async def list_exec_models():
        exec_models = [os.path.splitext(i)[0] for i in os.listdir(exec_models_dir) if not i.startswith("__")]
        for model in exec_models:
            dotted = ".".join([exec_path_dotted, model])

            # will store ModuleSpec as value, see: https://www.python.org/dev/peps/pep-0451/
            module = importlib.import_module(dotted)
            for _name, obj in inspect.getmembers(module):
                if "noobit_user" in str(obj) and inspect.isclass(obj):
                    runtime.Config.available_execution_models[model] = obj