import logging.config
import structlog


timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
pre_chain = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    timestamper,
]

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "noobit": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=True),
            "fmt": "%(message)s\n\r\033[2m---%(filename)s:%(funcName)s:line%(lineno)s\033[0m",
            "foreign_pre_chain": pre_chain,
        },
        "access": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=True),
            "foreign_pre_chain": pre_chain,
        },
        "uvicorn": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=True),
            "fmt": "%(message)s\n\r\033[2m---%(filename)s:%(funcName)s:line%(lineno)s\033[0m",
            "foreign_pre_chain": pre_chain,
        },
    },
    "handlers": {
        "noobit": {
            "formatter": "noobit",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "uvicorn": {
            "formatter": "uvicorn",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "default": {
            "class": "logging.NullHandler"
        }
    },
    "loggers": {
        # "noobit.processors.feed_handler": {"handlers": ["default"], "level": "INFO"},
        # "noobit.server.db_utils.account": {"handlers": ["default"], "level": "INFO"},
        # "noobit.server.db_utils.exchange": {"handlers": ["default"], "level": "INFO"},
        # "noobit.server.db_utils.strategy": {"handlers": ["default"], "level": "INFO"},
        # "noobit.server.db_utils.update_from_ws": {"handlers": ["default"], "level": "INFO"},
        # "noobit.server": {"handlers": ["default"], "level": "INFO"},
        # "noobit.feedhandler": {"handlers": ["default"], "level": "INFO"},
        # "noobit.cli": {"handlers": ["default"], "level": "INFO"},
        # "noobit.models": {"handlers": ["default"], "level": "INFO"},
        "noobit": {"handlers": ["noobit"], "level": "INFO"},
        "uvicorn": {"level": "INFO"},
        "uvicorn.error": {"handlers": ["uvicorn"], "level": "INFO", "propagate": True},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}
logging.config.dictConfig(LOGGING_CONFIG)

structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)