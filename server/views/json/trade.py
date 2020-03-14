from server import settings
import json
import datetime
import asyncio
import uuid
import logging
import stackprinter
from decimal import Decimal 
from typing import List

from server.views import APIRouter, Query, UJSONResponse
from models.orm_models import Order, Trade
from exchanges.mappings import rest_api_map


router = APIRouter()

#! Shoud we pass pair list as path parameter of query parameter
#! ==> queried like "domain/endpoint/pair" or "domain/endpoint?pair=..."

# ================================================================================
# ==== Private User Trading


@router.post('/place_order/{exchange}', response_class=UJSONResponse)
async def place_order(exchange: str,
                        pair: str = Query(..., title="Dash Separated Pair"),
                        side : str = Query(..., title="Direction of the trade (buy or sell)"),
                        ordertype: str = Query(..., title="Market/Limit/Stop Loss/Take Profit"),
                        price: float = Query(None, title="Price - Leave empty if order type is market"),
                        volume: float = Query(..., title="Volume of Order in lots"),
                        price2: float = Query(None, title="2nd Price - Depends on ordertype - Usually used for stops/take profits"),
                        leverage: float = Query(None, title="Leverage Used"),
                        validate: bool = Query(None, title="Only validate Order Input, without actually placing the order"),
                        retries: int = Query(None, title="Number of times to retry the request if it fails"),
                        start_time : int = Query(None, title="Start Time"),
                        expire_time : int = Query(None, title="Expire Time")
                        ):

    api = rest_api_map[exchange]()

    # no price = market order => we set order price to last close to calculate slippage later
    if not price:
        price = await api.get_ticker([pair])
        price = float(price.loc[pair.upper(), "close"][0])

    response = await api.place_order(pair=[pair],
                                     side=side,
                                     ordertype=ordertype,
                                     price=price,
                                     volume=volume,
                                     price2=price2,
                                     leverage=leverage,
                                     validate=validate
                                     )


    if not validate:
        exchange_order_id = response["txid"][0]
        # we need to append "id" to field name with foreign key: 
        # https://github.com/tortoise/tortoise-orm/issues/259
        order = await Order.create(exchange_id_id=settings.EXCHANGE_IDS_FROM_NAME[exchange],
                                   exchange_order_id=exchange_order_id,
                                   order_type=ordertype,
                                   order_side=side,
                                   volume=volume,
                                   price=price,  
                                   price2=price2,
                                   leverage=leverage,
                                   start_time=start_time,
                                   expire_time=expire_time,
                                   unique_id=uuid.uuid4().hex
                                   )

        # then we should go check if our order has been added to krakens open orders
        # note : this is only valid if we place a limit order, otherwise check trade history
        if 'limit' in ordertype:
            open_orders = await api.get_open_orders()
            try:
                checked_status = open_orders.loc[exchange_order_id, "status"]
                await Order.filter(exchange_order_id=exchange_order_id).update(status=checked_status)
            
            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))

            #TODO   how do we know when the order has been filled, so we can update the table later
            #TODO   do we just check on each candle interval ? for example we would check 4h later if the order has been processed and at what time ?
        
        if 'market' in ordertype:
            # kraken can be very slow to match orders
            await asyncio.sleep(2)
            trade_history = await api.get_user_trades_history()

            try:
                checked_trade = trade_history[trade_history["ordertxid"] == exchange_order_id]
                if not checked_trade.empty:

                    await Order.filter(exchange_order_id=exchange_order_id).update(
                                                                status="filled",
                                                                time_executed=checked_trade["time"],
                                                                )

                    # TODO  instead of querying db we could just return a repr when filtering above ?
                    order_id_query = await Order.filter(exchange_order_id=exchange_order_id).values("order_id")
                    order_id_value = order_id_query[0]["order_id"]

                    exchange_trade_id_array = checked_trade.index.values.tolist()
                    exchange_trade_id = exchange_trade_id_array[0]

                    slippage = abs(float(checked_trade["price"]) - price)
                    
                    await Trade.create(exchange_trade_id=exchange_trade_id,
                                       time_created=checked_trade["time"],
                                       trade_side=side,
                                       price=checked_trade["price"],                             
                                       volume=volume,
                                       fee=checked_trade["fee"], 
                                       slippage=slippage,
                                       order_id_id=order_id_value
                                       )
            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))

    return order


@router.post('/cancel_order/{exchange}', response_class=UJSONResponse)
async def cancel_order(exchange: str, 
                        txid: str = Query(..., title="ID of Order to cancel"),
                        retries: int = Query(None, title="Number of times to retry the request if it fails")
                        ):
    api = rest_api_map[exchange]()
    response = await api.cancel_order(txid=txid)
    return response 


#! Write Function to cancell all orders at once
#! Also write function to exit all positions at once

@router.post('/cancel_all_orders/{exchange}', response_class=UJSONResponse)
async def cancel_all_orders(exchange: str, 
                            retries: int = Query(None, title="Number of times to retry the request if it fails")
                            ):
    api = rest_api_map[exchange]()
    
    # open_orders = api.get_open_orders()
    
    # response = await api.cancel_order(txid=txid)
    # return response
    pass 

