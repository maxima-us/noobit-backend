import os
import signal,sys,time                          
import asyncio
import uvloop
import aioredis
import logging
import stackprinter
import functools
from contextlib import suppress


HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


class KrakenPrivateFeedConsumer:

    def __init__(self, sub_map: dict=None):
        """
        Sub Map keys are how we want to name the channel, value is the channel/pattern to subscribe to 
        """
        self.redis = None
        if sub_map is None:
            self.sub_map = {"events": "hearbeat:*", "status": "status:*", "data": "data:*", "system": "system:*"}
        else:
            self.sub_map = sub_map
        self.subd_channels = {}
        self.terminate = False


    async def subscribe(self):
        
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
            # print(f"consume from channel : {channel.name}")
            # print(f"        is active : {channel.is_active}")
            try:
                msg = await asyncio.wait_for(channel.get(), timeout=0.05)
                print(msg)
            except :
                pass
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2")) 
            
    
    async def on_tick(self, counter: int):


        await self.consume_from_channel(self.subd_channels["status"])
        await self.consume_from_channel(self.subd_channels["events"])
        await self.consume_from_channel(self.subd_channels["data"])
        await self.consume_from_channel(self.subd_channels["system"])

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


    async def serve(self):
        process_id = os.getpid()
        print(f"Consumer --- Started process {process_id}")
        self.install_signal_handlers()
        
        await self.subscribe()

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