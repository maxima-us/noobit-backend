from noobit import runtime
from noobit.logger.structlogger import get_logger


logger = get_logger(__name__)


async def public():
    for _exchange_name, fr_dict in runtime.Config.open_websockets.items():
        try:
            # dict value is abstract object, we need to instantiate it
            public_fr = fr_dict["public"]
            # connect method binds WebSocketClientProtocol to ws attribute
            try:
                await public_fr.close()
            except Exception as e:
                logger.exception(e)
        except Exception as e:
            logger.exception(e)


async def private():
    for _exchange_name, fr_dict in runtime.Config.open_websockets.items():
        try:
            # dict value is abstract object, we need to instantiate it
            private_fr = fr_dict["private"]
            # connect method binds WebSocketClientProtocol to ws attribute
            try:
                await private_fr.close()
            except Exception as e:
                logger.exception(e)
        except Exception as e:
            logger.exception(e)

