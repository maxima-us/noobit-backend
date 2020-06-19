"""
define what happens for each message received by redis sub
"""
import logging
import ujson

from noobit.server import settings
from noobit.models.orm import Order, Trade
from noobit.logger.structlogger import log_exception, log_exc_to_db

logger = logging.getLogger("uvicorn.error")


async def update_user_orders(exchange, message):

    try:

        if message is None:
            return

        msg = message.decode("utf-8")
        new_order = ujson.loads(msg)
        exchange_id = settings.EXCHANGE_IDS_FROM_NAME[exchange]

        # deprecated: new order now returns a list of pydantic Order models
        # for model in new_order:
            # if model["ordStatus"] == "pending-new":
            #     await Order.create(**model, exchange=exchange_id)
            # else:
            #     await Order.filter(order_id=model["orderID"]).update(**model)

        # ==> new order is now a single Order model

        new_order["targetStrategy_id"] = new_order.pop("targetStrategy")
        #!!! we need to account for foreign keys and suffix the key with _id
        #!   we also need to account for the fact that orderID is a unique field
        #!   so we need to check first if we have an entry for this orderID

        # .values() returns a list of dicts
        orderID_queryset = await Order.filter(orderID=new_order["orderID"]).values()
        logger.info(orderID_queryset)

        if new_order["ordStatus"] == "new":
            #check if there is an entry for this orderID
            if not orderID_queryset:
            # update dict to suffix foreign keys with _id
                await Order.create(**new_order, exchange_id=exchange_id)
            else:
                logger.info(f"Already an entry for {new_order['orderID']} in database")
        else:
            await Order.filter(orderID=new_order["orderID"]).update(**new_order, exchange_id=exchange_id)


    except Exception as e:
        log_exception(logger, e)
        await log_exc_to_db(logger, e)


async def update_user_trades(exchange, message):

    try:

        if message is None:
            return

        msg = message.decode("utf-8")
        new_trade = ujson.loads(msg)

        exchange_id = settings.EXCHANGE_IDS_FROM_NAME[exchange]

        # deprecated: doesnt return a TradesList anymore but single Trade Models
        # for model in new_trade:
        #     await Trade.create(**model, exchange=exchange_id)

        # ==> new order is now a single Trade model

        #!!! we need to account for foreign keys and suffix the key with _id
        new_trade["orderID_id"] = new_trade.pop("orderID")

        # check that orderID we pass already exists in order table
        orderID_queryset = await Order.filter(orderID=new_trade["orderID_id"]).values()
        logger.info(orderID_queryset)
        if orderID_queryset:
            await Trade.create(**new_trade, exchange_id=exchange_id)
        else:
            logger.info(f"No entry for trade {new_trade['trdMatchID']} - order {new_trade['orderID_id']}")

    except Exception as e:
        log_exception(logger, e)
        await log_exc_to_db(logger, e)


async def update_public_trades(exchange, message):
    try:
        if message is None:
            return

        msg = message.decode("utf-8")
        new_trade = ujson.loads(msg)
        logger.info(new_trade)

    except Exception as e:
        log_exception(logger, e)
        await log_exc_to_db(logger, e)


async def update_public_spread(exchange, message):
    try:
        if message is None:
            return

        msg = message.decode("utf-8")
        new_spread = ujson.loads(msg)
        # logging.info(new_spread)

    except Exception as e:
        log_exception(logger, e)
        await log_exc_to_db(logger, e)


async def update_public_instrument(exchange, message):
    try:
        if message is None:
            return

        msg = message.decode("utf-8")
        new_instrument = ujson.loads(msg)
        # logging.info(new_instrument)

    except Exception as e:
        log_exception(logger, e)
        await log_exc_to_db(logger, e)


async def update_public_orderbook(exchange, message):
    try:
        if message is None:
            return

        msg = message.decode("utf-8")
        new_book = ujson.loads(msg)
        # logging.info(new_book)

    except Exception as e:
        log_exception(logger, e)
        await log_exc_to_db(logger, e)
