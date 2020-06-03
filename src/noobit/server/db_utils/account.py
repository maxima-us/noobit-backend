import logging

import simplejson as ujson
import stackprinter

from noobit.server import settings
from noobit.models.orm import Exchange, Account
from noobit.exchanges.mappings import rest_api_map



async def record_new_account_update(event: str):
    """Insert new balance record into database and update redis cache

    Args:
        event (str) : event that triggered the update (periodic, trade ?)


    """

    for exchange_name, exchange_id in settings.EXCHANGE_IDS_FROM_NAME.items():

        #! update later
        api_key = f"{exchange_name}"
        api = rest_api_map[api_key]()


        #! check if this returns an OKResponse
        balances = await api.get_balances()
        if not balances.is_ok:
            return

        exposure = await api.get_exposure()
        if not exposure.is_ok:
            return

        open_positions = await api.get_open_positions(mode="by_id")
        if not open_positions.is_ok:
            return

        # redis = settings.AIOREDIS_POOL
        # TODO we could make each get request send the update value to redis ?
        # await redis.set(f"db:balance:holdings:{exchange_name}", ujson.dumps(holdings))
        # await redis.set(f"db:balance:positions:{exchange_name}", ujson.dumps(positions_vol))
        # await redis.set(f"db:balance:account_value:{exchange_name}", ujson.dumps(account_value))
        # await redis.set(f"db:balance:margin_level:{exchange_name}", ujson.dumps(margin_level))
        # await redis.set(f"db:balance:positions_unrealized:{exchange_name}", ujson.dumps(positions_pnl))

        #! WE STOPPED HERE, BLOCKED WITH A JSON SERIALIZING ISSUE
        #! HOW TO SERIALIZE DATETIME
        #! ==> lets just convert everything into time.time_ns instead
        try:
            await Account.create(
                event=event,
                exchange_id=ujson.dumps(exchange_id),
                balances=ujson.dumps(balances.value),
                exposure=ujson.dumps(exposure.value),
                open_positions=ujson.dumps(open_positions.value)
            )
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

        logging.warning(f"Balance : New event {event} for exchange {exchange_name} - db record inserted")




async def startup_account_table():

    try:
        exch_balances = await Account.all().values()
        # returns a list of dicts of the format {id: int , holdings:{}, exchange_id: int}

        # if Balance table is empty:
        if not exch_balances:
            logging.warning(f"Balance : db table is empty")

            try:
                exchanges = await Exchange.all().values()
                # returns a list of dicts of format {exchange_id: int, name: str}

                if not exchanges:
                    await instantiate_exchange_table()

            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))


    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))



async def instantiate_exchange_table():
    '''
    instantiate table if the passed dict is empty \t
    ==> we will need to define which exchanges need to be passed somehow and
    what their ids should be
    '''
    logging.warning(f"Exchange DBTable is empty")

    for exchange_name, exchange_id in settings.EXCHANGE_IDS_FROM_NAME.items():
        await Exchange.create(
            name=exchange_name,
            exchange_id=exchange_id
        )

        logging.warning(f"Added {exchange_name.upper()} to Exchange DBTable -- Exchange ID:{exchange_id}")

    logging.warning("Exchange DBTable instantiated")
