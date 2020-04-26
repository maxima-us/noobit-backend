import logging

import ujson
import stackprinter

from noobit.server import settings
from noobit.models.orm import Balance, Exchange
from noobit.exchanges.mappings import rest_api_map

# need to make this dynamic too
# from exchanges.kraken.utils.clean_data import open_positions_aggregated_by_pair, balance_remove_zero_values


def aggregate_open_positions(response: dict):
    """Aggregate open_positions by side and pair

    Args:
        response (dict): data received from get_open_positions request

    Returns:
        dict: 2 keys
            cost (dict) : position cost (in quote currency) aggregated by side and pair
                format {"long" : {<pair>:<cost>}, "short": {...}}
            volume (dict) : position volume (in base currency) aggregated by side and pair
                format {"long" : {<pair>:<vol>}, "short": {...}}
    """

    aggregated = {"cost": {"long": {}, "short": {}},
                  "volume": {"long": {}, "short": {}}
                  }

    for _pos_id, pos_info in response.items():
        pair = pos_info["pair"]
        side = pos_info["type"]
        if side == "buy":
            try:
                aggregated["volume"]["long"][pair] += pos_info["vol"]
            except KeyError:
                aggregated["volume"]["long"][pair] = pos_info["vol"]
            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))
            try:
                aggregated["cost"]["long"][pair] += pos_info["cost"]
            except KeyError:
                aggregated["cost"]["long"][pair] = pos_info["cost"]
            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))

        if side == "sell":
            try:
                aggregated["volume"]["short"][pair] += pos_info["vol"]
            except KeyError:
                aggregated["volume"]["short"][pair] = pos_info["vol"]
            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))
            try:
                aggregated["cost"]["short"][pair] += pos_info["cost"]
            except KeyError:
                aggregated["cost"]["short"][pair] = pos_info["cost"]
            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))


    return aggregated



async def record_new_balance_update(event: str):
    """Insert new balance record into database and update redis cache

    Args:
        event (str) : event that triggered the update (periodic, trade ?)


    """

    for exchange_name, exchange_id in settings.EXCHANGE_IDS_FROM_NAME.items():

        api = rest_api_map[exchange_name]()

        account_balance = await api.get_account_balance()
        trade_balance = await api.get_trade_balance()
        open_positions = await api.get_open_positions()

        # assets we are holding spot
        holdings = account_balance["data"]
        # account value in usd/eur or equivalent
        account_value = trade_balance["data"]["equivalent_balance"]
        # unrealized pnl of open_positions
        positions_pnl = trade_balance["data"]["positions_unrealized"]
        aggregated_pos = aggregate_open_positions(open_positions["data"])
        # positions aggregated by side, size is volume lots (for ex in BTC and not in USD)
        positions_vol = aggregated_pos["volume"]

        # ! counters can not have negatibe values so this does not work
        # exposure = Counter(holdings) + Counter(positions_vol["long"]) - Counter(positions_vol["short"])

        margin_level = trade_balance["data"]["margin_level"]

        redis = settings.AIOREDIS_POOL

        # TODO we could make each get request send the update value to redis ?
        await redis.set(f"db:balance:holdings:{exchange_name}", ujson.dumps(holdings))
        await redis.set(f"db:balance:positions:{exchange_name}", ujson.dumps(positions_vol))
        await redis.set(f"db:balance:account_value:{exchange_name}", ujson.dumps(account_value))
        await redis.set(f"db:balance:margin_level:{exchange_name}", ujson.dumps(margin_level))
        await redis.set(f"db:balance:positions_unrealized:{exchange_name}", ujson.dumps(positions_pnl))

        try:
            await Balance.create(
                exchange_id=exchange_id,
                event=event,
                holdings=holdings,
                positions=positions_vol,
                positions_unrealized=positions_pnl,
                account_value=account_value,
                margin=margin_level,
                # exposure=0
            )
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

        logging.warning(f"Balance : New event {event} for exchange {exchange_name} - db record inserted")



async def startup_balance_table():

    try:
        exch_balances = await Balance.all().values()
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
