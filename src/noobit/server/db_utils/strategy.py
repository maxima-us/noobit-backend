import logging

from noobit.models.orm import Strategy
from noobit.logger.structlogger import log_exception, log_exc_to_db

logger = logging.getLogger("uvicorn.error")


async def startup_strategy_table():

    try:
        strategies = await Strategy.all().values()
        # returns a list of dicts of the format {id: int , holdings:{}, exchange_id: int}

        # if Balance table is empty:
        if not strategies:
            logger.warning(f"Strategy : db table is empty")

            try:
                await Strategy.create(
                    strategy_id=0,
                    name="discretionary",
                    description="a catch-all strategy for all trades that are not placed by one of our strategies"
                )

            except Exception as e:
                log_exception(logger, e)
                await log_exc_to_db(logger, e)

    except Exception as e:
        log_exception(logger, e)
        await log_exc_to_db(logger, e)