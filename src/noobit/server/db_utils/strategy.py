import logging

import stackprinter

from noobit.models.orm import Strategy


async def startup_strategy_table():

    try:
        strategies = await Strategy.all().values()
        # returns a list of dicts of the format {id: int , holdings:{}, exchange_id: int}

        # if Balance table is empty:
        if not strategies:
            logging.warning(f"Strategy : db table is empty")

            try:
                await Strategy.create(
                    strategy_id=0,
                    name="discretionary",
                    type="discretionary",
                    description="a catch-all strategy for all trades that are not placed by one of our strategies"
                )

            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))
