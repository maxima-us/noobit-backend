import logging
import uuid

import ujson
import stackprinter

from noobit.server import settings
from noobit.models.orm import Order, Trade
from noobit.exchanges.mappings import rest_api_map


async def update_user_orders(exchange, message):


    try:

            # raw message will be of format :
            #         b'{"OURTBZ-BO9CD-MHTOA6":{"status":"canceled","cost":"0.00000",
            #                                            "vol_exec":"0.00000000","fee":"0.00000",
            #                                            "avg_price":"0.00000"}
            #            }

            #  or
            #      b'{"OUZTAZ-BO7AD-MDSOA6":{"avg_price":"0.00000","cost":"0.00000",
            #                                         "descr":{"close":null,"leverage":null,
            #                                                  "order":"buy 10.00000000 XBT\\/USD @ limit 10.00000",
            #                                                   "ordertype":"limit","pair":"XBT\\/USD","price":"10.00000",
            #                                                   "price2":"0.00000","type":"buy"},
            #                                          "expiretm":null,"fee":"0.00000","limitprice":"0.00000","misc":"",
            #                                          "oflags":"fciq","opentm":"1584396450.270295","refid":null,"starttm":null,
            #                                          "status":"pending","stopprice":"0.00000","userref":0,
            #                                          "vol":"10.00000000","vol_exec":"0.00000000"}
            #         }

            # or
            #       b'{"OUZTAZ-BO7AD-MDSOA6":{"status":"open"}}

        if message is None:
            return

        msg = message.decode("utf-8")
        new_order = ujson.loads(msg)

        for order_id, order_info in new_order.items():


            if order_info["status"] == "pending":

                # we receive a userref from the order passed that should correspond to the strat that placed it
                # if we did not receive one then we must assume it was a discretionary trade (which correponds to id=0 in strat db table)

                strat_id = order_info.get("userref", 0)
                pair = order_info["descr"]["pair"].replace("/", "-")

                await Order.create(order_id=order_id,
                                   pair=pair,
                                   type=order_info["descr"]["ordertype"],
                                   side=order_info["descr"]["type"],
                                   open_time=10,
                                   start_time=order_info["starttm"],
                                   expire_time=order_info["expiretm"],
                                   volume_total=order_info["vol"],
                                   volume_filled=order_info["vol_exec"],
                                   price_limit=order_info["descr"]["price"],
                                   price2=order_info["descr"]["price2"],
                                   leverage=order_info["descr"]["leverage"],
                                   fill_price=order_info["avg_price"],
                                   strategy_id_id=strat_id,
                                   )
                logging.info(f"Order : {order_id} is pending - db records created")


            if order_info["status"] == "open":
                filled = order_info.get("vol_exec", 0)

                # for market order the price we receive from the api is = 0
                # therefore we set price to the ticker price at current time
                if order_info["descr"]["ordertype"] == "market":
                    api = rest_api_map[exchange]()
                    api.session = settings.SESSION
                    ticker = await api.get_ticker([pair])
                    price = ticker["data"][pair]["close"]
                    await Order.filter(exchange_order_id=order_id).update(status="open", filled=filled, price=price)

                else:
                    await Order.filter(exchange_order_id=order_id).update(status="open", filled=filled)


                logging.info(f"Order : {order_id} is open - db records updated")

            if order_info["status"] == "canceled":
                await Order.filter(exchange_order_id=order_id).update(status="canceled")
                logging.info(f"Order : {order_id} is canceled - db records updated")


    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))



async def update_user_trades(exchange, message):

    try:
        # raw message will be of format
        #        b'{"TDLH43-DVQXD-2KHVYY": {"cost": "1000000.00000",
        #                                    "fee": "600.00000",
        #                                    "margin": "0.00000",
        #                                    "ordertxid": "TDLH43-DVQXD-2KHVYY",
        #                                    "ordertype": "limit",
        #                                    "pair": "XBT/EUR",
        #                                    "postxid": "OGTT3Y-C6I3P-XRI6HX",
        #                                    "price": "100000.00000",
        #                                    "time": "1560520332.914664",
        #                                    "type": "buy",
        #                                    "vol": "1000000000.00000000"
        #                                    }
        #          }

        if message is None:
            return

        msg = message.decode("utf-8")
        new_trade = ujson.loads(msg)

        for trade_id, trade_info in new_trade.items():

            exchange_id = settings.EXCHANGE_IDS_FROM_NAME[exchange]
            corresponding_order_id = trade_info["ordertxid"]
            order_price = await Order.filter(exchange_order_id=corresponding_order_id).values("price")
            trade_price = trade_info["price"]
            slippage = trade_price - order_price

            await Trade.create(exchange_id_id=exchange_id,
                               exchange_trade_id=trade_id,
                               time_created=trade_info["time"],
                               trade_side=trade_info["type"],
                               pair=trade_info["pair"].replace("/", "-"),
                               price=trade_price,
                               volume=trade_info["vol"],
                               fee=trade_info["fee"],
                               slippage=slippage,
                               order_id_id=corresponding_order_id
                               )


    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))


async def update_public_trades(exchange, message):
    try:
        if message is None:
            return

        msg = message.decode("utf-8")
        new_trade = ujson.loads(msg)
        logging.info(new_trade)

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))


async def update_public_spread(exchange, message):
    try:
        if message is None:
            return

        msg = message.decode("utf-8")
        new_trade = ujson.loads(msg)
        logging.info(new_trade)

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))