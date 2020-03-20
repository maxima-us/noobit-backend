import os
import signal,sys,time                          
import functools
import asyncio
import logging
import uuid

import ujson
import uvloop
import aioredis
import stackprinter

from server import settings
from models.orm_models import Order, Trade



class FeedConsumer:

    def __init__(self, sub_map: dict=None):
        """
        Sub Map keys are how we want to name the channel, value is the channel/pattern to subscribe to 
        """
        self.redis = None
        if sub_map is None:
            self.sub_map = {"events": "heartbeat:*", 
                            "status": "status:*", 
                            "order_snapshot": "data:snapshot:kraken:openOrders",
                            "order_updates": "data:update:kraken:openOrders",
                            "trade_snapshot": "data:snapshot:kraken:ownTrades",
                            "trade_updates": "data:update:kraken:ownTrades",
                            "system": "system:*"}
        else:
            self.sub_map = sub_map
        self.subd_channels = {}
        self.terminate = False



    async def subscribe(self):
        
        # self.redis = await aioredis.create_redis_pool('redis://localhost')
        self.redis = settings.AIOREDIS_POOL 
        
        try:
            for key, channel_name in self.sub_map.items():
                res = await self.redis.psubscribe(channel_name)
                # subscribe/psub always return a list
                self.subd_channels[key] = res[0]
                assert isinstance(self.subd_channels[key], aioredis.Channel)

        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

    
    async def handle_msg(self, msg):
        print(f"Consumer --- Got message : {msg}")
    


    async def consume_from_channel(self, channel: aioredis.Channel):
        
        try:
            # print(f"consume from channel : {channel.name}")
            # print(f"        is active : {channel.is_active}")
            try:
                msg = await asyncio.wait_for(channel.get(), timeout=0.1)
                return msg
            except :
                pass
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2")) 
            


    async def update_orders(self, exchange):

        channel = self.subd_channels["order_updates"]
        bytemsg = None
        bytechan = None
        
        try:

            try: 
                bytechan, bytemsg = await asyncio.wait_for(channel.get(), timeout=0.1)
            except:
                pass

            if bytemsg is None:
                return
                # raw message will be tuple of format :
                #        (b'data:update:kraken:openOrders', 
                #         b'[{"OURTBZ-BO9CD-MHTOA6":{"status":"canceled","cost":"0.00000",
                #                                            "vol_exec":"0.00000000","fee":"0.00000",
                #                                            "avg_price":"0.00000"}
                #            }]
                #          )

                #  or
                #     (b'data:update:kraken:openOrders', 
                #      b'[{"OUZTAZ-BO7AD-MDSOA6":{"avg_price":"0.00000","cost":"0.00000",
                #                                         "descr":{"close":null,"leverage":null,
                #                                                  "order":"buy 10.00000000 XBT\\/USD @ limit 10.00000",
                #                                                   "ordertype":"limit","pair":"XBT\\/USD","price":"10.00000",
                #                                                   "price2":"0.00000","type":"buy"},
                #                                          "expiretm":null,"fee":"0.00000","limitprice":"0.00000","misc":"",
                #                                          "oflags":"fciq","opentm":"1584396450.270295","refid":null,"starttm":null,
                #                                          "status":"pending","stopprice":"0.00000","userref":0,
                #                                          "vol":"10.00000000","vol_exec":"0.00000000"}
                #         }]
                #       )

                # or 
                #      (b'data:update:kraken:openOrders', 
                #       b'[{"OUZTAZ-BO7AD-MDSOA6":{"status":"open"}}]
                #       )


            msg = bytemsg.decode("utf-8")
            new_order = ujson.loads(msg)

            for order_id, order_info in new_order.items():

                if order_info["status"] == "pending":

                    # we receive a userref from the order passed that should correspond to the strat that placed it
                    # if we did not receive one then we must assume it was a discretionary trade (which correponds to id=0 in strat db table)

                    strat_id = order_info.get("userref", 0)


                    await Order.create(exchange_id_id=settings.EXCHANGE_IDS_FROM_NAME[exchange],
                                            exchange_order_id=order_id,
                                            strategy_id_id=strat_id,
                                            order_type=order_info["descr"]["ordertype"],
                                            order_side=order_info["descr"]["type"],
                                            pair=order_info["descr"]["pair"].replace("/", "-"),
                                            price=order_info["descr"]["price"],  
                                            price2=order_info["descr"]["price2"],
                                            leverage=order_info["descr"]["leverage"],
                                            volume=order_info["vol"],
                                            filled=order_info["vol_exec"],
                                            fill_price=order_info["avg_price"],
                                            open_time=order_info["opentm"],
                                            start_time=order_info["starttm"],
                                            expire_time=order_info["expiretm"],
                                            unique_id=uuid.uuid4().hex
                                            )
                    logging.info(f"Order : {order_id} is pending - db records created")

                if order_info["status"] == "open":

                    filled = order_info.get("vol_exec", 0)

                    await Order.filter(exchange_order_id=order_id).update(status="open", filled=filled)
                    logging.info(f"Order : {order_id} is open - db records updated")

                if order_info["status"] == "canceled":
                    await Order.filter(exchange_order_id=order_id).update(status="canceled")
                    logging.info(f"Order : {order_id} is canceled - db records updated")


        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

    

    async def update_trades(self, exchange):

        channel = self.subd_channels["trade_updates"]
        bytemsg = None
        bytechan = None


        try:
            try: 
                bytechan, bytemsg = await asyncio.wait_for(channel.get(), timeout=0.1)
            except:
                pass
            
            if bytemsg is None:
                return

            # raw message will be tuple of format
            #       (b'data:update:kraken:openOrders', 
            #        b'[{"TDLH43-DVQXD-2KHVYY": {"cost": "1000000.00000",
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
            #          }]
            #        )
            
            msg = bytemsg.decode("utf-8")
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
    




    # async def on_tick(self, counter: int):

    #     await self.consume_from_channel(self.subd_channels["status"])
    #     await self.consume_from_channel(self.subd_channels["events"])
    #     await self.consume_from_channel(self.subd_channels["data"])
    #     await self.consume_from_channel(self.subd_channels["system"])

    #     if self.terminate:
    #         return True
    #     return False

