import sys
import logging
# import logging.config
import asyncio

import structlog
import stackprinter

from tortoise import Tortoise

# from noobit import runtime_config
from noobit.server import settings as runtime_config
from noobit_user import get_abs_path
from noobit.models.orm.errors import ErrorLog
from noobit.logger import config



def get_logger(name: str, level=logging.INFO, exception_style: str = "darkbg2"):
    stackprinter.set_excepthook(style=exception_style)
    root_logger = logging.getLogger(name)
    return root_logger

def get_structlogger(name: str, exception_style: str = "darkbg2"):
    stackprinter.set_excepthook(style=exception_style)
    root_logger = structlog.getLogger(name)
    return root_logger


#================================================================================
#================================================================================
#================================================================================
#================================================================================




def get_blogger(name: str, level=logging.INFO, exception_style: str = "darkbg2"):
    stackprinter.set_excepthook(style=exception_style)

    ''' this func has exactly the same result as the code above'''

    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S"),
            structlog.processors.StackInfoRenderer(),
            # structlog.processors.ExceptionPrettyPrinter(),
            # SentryProcessor(level=logging.ERROR),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()  # <===
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # formatter = structlog.stdlib.ProcessorFormatter(
    #     processor=structlog.dev.ConsoleRenderer(),
    # )


    logging.basicConfig(
        format="%(message)s\n\r\033[2m---%(filename)s:%(funcName)s:line%(lineno)s\033[0m",
        stream=sys.stdout,
        level=level,
    )

    # handler = logging.StreamHandler()
    # handler.setFormatter(formatter)
    # root_logger = logging.getLogger()
    # root_logger.addHandler(handler)
    # root_logger.setLevel(logging.INFO)


    root_logger = structlog.get_logger(name)

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(get_connection(logger=root_logger))

    return root_logger



#================================================================================
#================================================================================
#================================================================================
#================================================================================




user_dir = get_abs_path()

config = None
config_file = None
db_url=f"sqlite://{user_dir}/data/fastapi.db"
modules={"models": ["noobit.models.orm"]}
generate_schemas=True


async def get_connection(logger):
    try:
        await Tortoise.init(config=config, config_file=config_file, db_url=db_url, modules=modules)
    except Exception as e:
        logger.warning(e)
        raise e
        # logging.info("Tortoise-ORM started, %s, %s", Tortoise._connections, Tortoise.apps)
    if generate_schemas:
        try:
            logging.info("Tortoise-ORM generating schema")
            await Tortoise.generate_schemas()
        except Exception as e:
            logger.warning(e)
            raise e




#================================================================================
#================================================================================
#================================================================================
#================================================================================
#================================================================================




def log_exception(logger: object, msg: Exception):
    stack = stackprinter.format(msg, style="darkbg2")
    logger.exception(stack)


async def log_exc_to_db(logger: object, msg: Exception):

    # ErrorLog being an ORM Model :
    if not isinstance(msg, str):
        stack = stackprinter.format(msg)
        logger.exception(stackprinter.format(msg, style="darkbg2"))
        if isinstance(msg, Exception):
            json = {"error": str(msg)}
    else:
        return
    await ErrorLog.create(json=json, stack=stack)
