"""
===> For now lets put this aside
"""


import logging
import uuid
from decimal import Decimal

import stackprinter

from noobit.server import settings
from noobit.models.orm import Trade, Order
from noobit.exchanges.mappings import rest_api_map


async def startup_trades_table():

    for exchange_name, exchange_id in settings.EXCHANGE_IDS_FROM_NAME.items():

        try:
            api = rest_api_map[exchange_name]()
            user_trades = await api.get_user_trades(start=0)

            for order_id, trade_info in user_trades["data"].items():

                ordertxid = trade_info["ordertxid"]

                # first check if the corresponding order is already in db
                order = await Order.filter(order_id=ordertxid).values()

                # if it is not, then we must fetch the info from api
                if not order:
                    #! IMPLEMENT GET ORDER INFO METHOD IN OUR API
                    order_info = await api.get_order_info(ordertxid)
                    avg_fill = order_info["price"]
                    order_price = order_info["descr"]["price"]
                    leverage = 0 if order_info["descr"]["leverage"] == "none" else order_info["descr"]["leverage"].split(":")[0]

                    await Order.create(exchange_id_id=exchange_id,
                                       exchange_order_id=order_id,
                                       strategy_id_id=0,
                                       status="closed",
                                       order_type=order_info["descr"]["ordertype"],
                                       order_side=order_info["descr"]["type"],
                                       pair=order_info["descr"]["pair"].replace("/", "-"),
                                       price=order_price,
                                       price2=order_info["descr"]["price2"],
                                       leverage=leverage,
                                       volume=order_info["vol"],
                                       filled=order_info["vol_exec"],
                                       fill_price=avg_fill,
                                       open_time=order_info["opentm"],
                                       start_time=order_info["starttm"],
                                       expire_time=order_info["expiretm"],
                                       unique_id=uuid.uuid4()
                                       )
                else:
                    order_price = order["price"]


                user_trades = await Trade.create(
                    exchange_id=exchange_id,
                    exchange_trade_id=order_id,
                    unique_id=str(uuid.uuid4()),
                    time_created=trade_info["time"],
                    trade_side=trade_info["type"],
                    pair=trade_info["pair"],
                    price=trade_info["price"],
                    volume=trade_info["vol"],
                    fee=trade_info["fee"],
                    slippage=Decimal(trade_info["price"]) - Decimal(order_price),
                    leverage=0,
                    # order_id=trade_info["ordertxid"]
                    order_id=1
                    #! the issue here is we will have to fetch all the order info and insert before
                    #!   being able to create insert the trade, otherwise the FK relation can not be
                    #!   created (trade FK will try to refer to an inexistant order)
                )

        except Exception as e:
            logging.error(trade_info["ordertxid"])
            logging.error(stackprinter.format(e, style="darkbg2", add_summary=True))