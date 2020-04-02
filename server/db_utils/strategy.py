import logging

import stackprinter

from models.orm_models.strategy import Strategy


async def startup_strategy_table():

    try:
        strategies = await Strategy.all().values()
        # returns a list of dicts of the format {id: int , holdings:{}, exchange_id: int}

        # if Balance table is empty:
        if not strategies:
            logging.warning(f"Strategy : db table is empty")

            try:
                await Strategy.create(
                    id=0,
                    name="discretionary",
                    type="discretionary"
                )

            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))
