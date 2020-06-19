from noobit.logging.structlogger import get_logger, log_exception
from blessings import Terminal

t = Terminal()
logger = get_logger("uvicorn")

for i in range(10):
    msg = f"int is {t.red(str(i))}"
    logger.info(msg)