import sys
import inspect
import logging
import structlog
import stackprinter

# def get_logger(name):
#     configure_logging(name)
#     logger = structlog.get_logger(name)
#     return logger


# def configure_logging(name):

#     """Configure logging and structlog.
#     """

#     shared_processors = [
#                         structlog.stdlib.add_log_level,
#                         structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
#                         structlog.stdlib.add_logger_name
#                         ]

#     structlog.configure(processors=shared_processors +
#                         [structlog.stdlib.ProcessorFormatter.wrap_for_formatter,],
#                         logger_factory=structlog.stdlib.LoggerFactory(),
#                         cache_logger_on_first_use=True,
#                         )

#     formatter = structlog.stdlib.ProcessorFormatter(processor=structlog.dev.ConsoleRenderer(),
#                                                    foreign_pre_chain=shared_processors,
#                                                    )


#     handler = logging.StreamHandler()
#     handler.setFormatter(formatter)
#     root_logger = logging.getLogger(name)
#     root_logger.addHandler(handler)
#     root_logger.setLevel(logging.INFO)


def get_logger(name: str, level=logging.INFO, exception_style: str="darkbg2"):
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
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()  # <===
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s\n\r:%(filename)s:%(funcName)s:line%(lineno)s",
        stream=sys.stdout,
        level=level,
    )

    root_logger = structlog.get_logger(name)
    return root_logger




def log_exception(logger: object, msg: str):
    return logger.exception(stackprinter.format(msg, style="darkbg2"))
