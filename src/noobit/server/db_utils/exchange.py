import logging

from noobit.server import settings
from noobit.models.orm import Exchange
from noobit.logger.structlogger import log_exception, log_exc_to_db

logger = logging.getLogger("uvicorn.error")

async def startup_exchange_table():
    '''
    instantiate table if the passed dict is empty \t
    ==> we will need to define which exchanges need to be passed somehow and
    what their ids should be
    '''
    logger.warning(f"Exchange DBTable is empty")

    for exchange_name, exchange_id in settings.EXCHANGE_IDS_FROM_NAME.items():

        try:
            values = await Exchange.filter(name=exchange_name).values()
            logger.error(f"Exchanges : {values}")
        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)

        if not values:
            try:
                await Exchange.create(
                    id=exchange_id,
                    name=exchange_name
                )
            except Exception as e:
                log_exception(logger, e)
                await log_exc_to_db(logger, e)

        logger.warning(f"Added {exchange_name.upper()} to Exchange DBTable -- Exchange ID:{exchange_id}")

    logger.warning("Exchange DBTable instantiated")