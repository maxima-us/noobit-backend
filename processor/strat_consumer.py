import os
import uuid
import signal,sys,time                          
import asyncio
import uvloop
import aioredis
import logging
import stackprinter
import functools
from contextlib import suppress
from collections import deque


HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


class KrakenStratConsumer:

    def __init__(self, ws_token, sub_map: dict=None):
        """
        Sub Map keys are how we want to name the channel, value is the channel/pattern to subscribe to 
        """

        # we need to connect to private kraken WS
        self.ws_token = ws_token        # TODO  ==> actually server should send it over redis

        self.redis = None
        if sub_map is None:
            self.sub_map = {"events": "events", "status": "status", "data": "data:*"}
        else:
            self.sub_map = sub_map
        self.subd_channels = {}
        self.terminate = False

        self.pair = None
        self.exchange = None

        # this will store previous tick values to be used in execution logic
        # how many ticks back to we want to look ?
        self.ohlc = deque(maxlen=40)

        # we store current orders and track them 
        # order key 
        # order value = tuple (order volume, filled volume)
        # on each tick we update their filled volume
        self.open_orders = {}



    async def subscribe_redis_channels(self):
        
        self.redis = await aioredis.create_redis_pool('redis://localhost')
        
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
            # some data channels might not send any data for some period
            # if we don't time out we may block the loop
            try:
                msg = await asyncio.wait_for(channel.get(), timeout=0.01)
                await handle_msg(msg)
            except :
                pass
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2")) 
            

    async def pre_tick(self):
        """process data to be used by tick logic
        """

        # consume openOrders websockets to checked filled volume
        open_orders = await self.consume_from_channel(self.subd_channels["open_orders"])

        # get latest msg from channel
        events = await self.consume_from_channel(self.subd_channels["events"])
        data = await self.consume_from_channel(self.subd_channels["data"])
        ohlc = await self.consume_from_channel(self.subd_channels["ohlc"])

        # add to deque, that way we can store a few of the past values
        # we append to the left, so the most recent is always at [0], next one at [1] etc
        # similar to tradingview
        self.ohlc.appendleft(ohlc)

        # remove filled orders from open_orders dict
        self.open_orders = {key:vtuple for key, vtuple in self.open_orders.items() if vtuple[0]>vtuple[1]}


    async def execution(self):
        """
        """

        # check open orders, get remaining volume 
        # if we want to update order (for ex if we are chasing price):
        #       ==> cancel order over websocket
        #       ==> add new order over websocket with remaining volume, at new price


        for order in self.open_orders:
            pass


    def buy_btc(self):
        
        if self.ohlc[0] > self.ohlc[1]:
            order_uuid = uuid.uuid4().hex
            # maybe we want to dynamically determine volume
            volume = 1  
            self.open_orders[order_uuid] = (volume, 0)
            data = {"uuid": order_uuid,
                    "side": "buy",
                    "type": "limit",
                    "volume": volume,
                    "pair": "XBT-USD",
                    "price": self.price[0] - 1
            }
            return data


    async def on_tick(self, counter: int):
        await self.pre_tick()
        
        # TODO  copy counter check function from main_server to know if we are at a checkpoint 
        # TODO  (assuming our strategy is only placing orders at certain intervals)
        
        await self.trade_signals()

        #! this needs to be in the execution coroutine
        # await self.redis.publish("orders:add", data)

        await self.execution()

        if self.terminate:
            return True
        return False


    async def main_loop(self):
        counter = 0
        should_exit = await self.on_tick(counter)
        while not should_exit:
            counter += 1

            # do we need to change 864000 to some other number ?
            counter = counter % 864000
            await asyncio.sleep(1)
            should_exit = await self.on_tick(counter)
            print(f"main loop {counter}")


    async def serve(self):
        process_id = os.getpid()
        print(f"Consumer --- Started process {process_id}")
        self.install_signal_handlers()
        
        await self.subscribe_redis_channels()

        # tasks = [self.consume_from_channel(channel) for _, channel in self.subd_channels.items()]
        # done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # for name , channel in self.subd_channels.items(): 
        #     await self.consume_from_channel(channel)
        if self.terminate:
            return
        await self.main_loop()
        
        print("Consumer --- Shutting down")
        print("Consumer --- Closing redis")
        self.redis.close()
        await self.redis.wait_closed()
        print("Consumer --- Shutdown complete")


    def run(self):
        uvloop.install()
        asyncio.run(self.serve())
        # try:
        #     asyncio.run(self.main())
        # except KeyboardInterrupt:
        #     loop = asyncio.get_event_loop()
        #     # Let's also cancel all running tasks:
        #     pending = asyncio.Task.all_tasks()
        #     for task in pending:
        #         task.cancel()
        #         # Now we should await task to execute it's cancellation.
        #         # Cancelled task raises asyncio.CancelledError that we can suppress:
        #         with suppress(asyncio.CancelledError):
        #             loop.run_until_complete(task)
    
    def install_signal_handlers(self):
        loop = asyncio.get_event_loop()

        try:
            for sig in HANDLED_SIGNALS:
                loop.add_signal_handler(sig, self.handle_exit, sig, None)
                # loop.add_signal_handler(sig, lambda sig=sig: asyncio.create_task(self.shutdown(sig, loop)))
                # loop.add_signal_handler(sig, lambda sig=sig: asyncio.create_task(self.another_shutdown(sig, loop)))
        except NotImplementedError as exc:
            # Windows
            for sig in HANDLED_SIGNALS:
                signal.signal(sig, self.handle_exit)


    def handle_exit(self, sig, frame):
        self.terminate = True


    # async def shutdown(self, signal, loop):
    #     """Cleanup tasks tied to the service's shutdown.
    #     """
    #     logging.info(f"Received exit signal {signal.name}...")
    #     logging.info("Closing database connections")
    #     logging.info("Nacking outstanding messages")
    #     tasks = [t for t in asyncio.all_tasks() if t is not
    #             asyncio.current_task()]

    #     [task.cancel() for task in tasks]

    #     logging.info(f"Cancelling {len(tasks)} outstanding tasks")
    #     await asyncio.gather(*tasks, return_exceptions=True)
    #     logging.info(f"Flushing metrics")


    # async def another_shutdown(self, sig, loop):
    #     print('caught {0}'.format(sig.name))
    #     tasks = [task for task in asyncio.Task.all_tasks() if task is not
    #             asyncio.tasks.Task.current_task()]
    #     list(map(lambda task: task.cancel(), tasks))
    #     results = await asyncio.gather(*tasks, return_exceptions=True)
    #     print('finished awaiting cancelled tasks, results: {0}'.format(results))
    #     loop.stop()
        


# if __name__ == "__main__":
#     uvloop.install()
#     asyncio.run(consume())