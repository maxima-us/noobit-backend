import logging

import stackprinter

from noobit.server import settings
from noobit.models.orm import Exchange

async def startup_exchange_table():
    '''
    instantiate table if the passed dict is empty \t
    ==> we will need to define which exchanges need to be passed somehow and
    what their ids should be
    '''
    logging.warning(f"Exchange DBTable is empty")

    for exchange_name, exchange_id in settings.EXCHANGE_IDS_FROM_NAME.items():

        try:
            values = await Exchange.filter(name=exchange_name).values()
            logging.error(f"Exchanges : {values}")
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

        if not values:
            try:
                await Exchange.create(
                    id=exchange_id,
                    name=exchange_name
                )
            except Exception as e:
                logging.error(stackprinter.format(e, style='darkbg2'))

        logging.warning(f"Added {exchange_name.upper()} to Exchange DBTable -- Exchange ID:{exchange_id}")

    logging.warning("Exchange DBTable instantiated")