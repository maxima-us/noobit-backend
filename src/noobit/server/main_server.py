'''
Hack uvicorn main file to launch our own service on top of it
'''
import asyncio
import copy
import functools
import os
import platform
import signal
import socket
import sys
import time
from email.utils import formatdate
import logging

import aioredis
import click
from blessings import Terminal
import uvicorn
from uvicorn.supervisors import Multiprocess, StatReload

#!! not sure V
from uvicorn import Config

from noobit.server import settings
from noobit.server.db_utils.account import record_new_account_update
from noobit.server.db_utils.exchange import startup_exchange_table
from noobit.server.db_utils.strategy import startup_strategy_table
from noobit.server.db_utils.update_from_ws import (
    update_user_trades,
    update_user_orders,
    update_public_trades,
    update_public_spread,
    update_public_orderbook,
    update_public_instrument
)
from noobit.server.app_startup.monit import startup_monit
from noobit.server.monitor.heartbeat import Heartbeat


HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)

# from noobit.logger.structlogger import get_logger
# logger = logging.getLogger('uvicorn.error')
logger = logging.getLogger("uvicorn.error")
t = Terminal()




# =====================================================================================
# =====================================================================================

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(
        "Running uvicorn %s with %s %s on %s"
        % (
            uvicorn.__version__,
            platform.python_implementation(),
            platform.python_version(),
            platform.system(),
        )
    )
    ctx.exit()


# =========================================================================================
# =========================================================================================


def run(app, **kwargs):
    # Config.configure_logging = functools.partial(override_configure_logging, Config) #overwrite uvicorn method
    # kwargs["log_config"] = LOGGING_CONFIG #! overwrite
    config = Config(app, **kwargs)
    config.backlog = 2048           #! for some reason we need to specify this
    # config.log_config = LOGGING_CONFIG  #! overwrite write our own
    server = Server(config=config)


    if (config.reload or config.workers > 1) and not isinstance(app, str):
        logger.warn(
            "You must pass the application as an import string to enable 'reload' or 'workers'."
        )
        sys.exit(1)

    if config.should_reload:
        sock = config.bind_socket()
        supervisor = StatReload(config, target=server.run, sockets=[sock])
        supervisor.run()
    elif config.workers > 1:
        sock = config.bind_socket()
        supervisor = Multiprocess(config, target=server.run, sockets=[sock])
        supervisor.run()
    else:
        server.run()


class ServerState:
    """
    Shared servers state that is available between all protocol instances.
    """

    def __init__(self):
        self.total_requests = 0
        self.connections = set()
        self.tasks = set()
        self.default_headers = []


class Server:
    def __init__(self, config, sub_map=None):
        self.config = config
        self.server_state = ServerState()

        # status
        self.started = False
        self.should_exit = False
        self.force_exit = False
        self.last_notified = 0

        # heartbeat
        self.heartbeat = None

        # websockets
        # self.open_websockets = {}
        # self.private_ws = None
        # self.public_ws = None
        self.redis_sub = None
        self.aioredis_pool = None

        # redis
        self.redis_tasks = []
        self.subscribed_channels = {}
        if sub_map is None:
            # redis channels are case sensitive
            self.sub_map = {"public_heartbeat": "ws:public:heartbeat:*",
                            "public_status": "ws:public:status:*",
                            "public_system": "ws:public:system:*",
                            "public_trade_updates": "ws:public:data:trade:update:kraken:*",
                            "public_instrument_updates": "ws:public:data:instrument:update:kraken:XBT-USD",
                            "public_orderbook_updates": "ws:public:data:orderbook:update:kraken:*",
                            "private_heartbeat": "ws:private:heartbeat",
                            "private_status": "ws:private:status:*",
                            "private_system": "ws:private:system:*",
                            "private_order_updates": "ws:private:data:order:update:kraken:*",
                            "private_trade_updates": "ws:private:data:trade:update:kraken:*",
                            }
        else:
            self.sub_map = sub_map


    def run(self, sockets=None):
        self.config.setup_event_loop()
        loop = asyncio.get_event_loop()
        # loop.run_until_complete(self.startup_feed_consumer())
        # loop.run_until_complete(self.serve(sockets=sockets))
        loop.run_until_complete(self.main(sockets))



    async def main(self, sockets):
        # await self.subscribe_redis_channel()
        await self.setup_redis_sub()

        results = await asyncio.gather(*self.redis_tasks, self.serve(sockets=sockets))
        return results



    async def serve(self, sockets=None):
        process_id = os.getpid()

        config = self.config
        if not config.loaded:
            config.load()

        self.lifespan = config.lifespan_class(config)

        # self.lifespan.logger.handlers.clear()
        # loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        # for lgr in copy.copy(loggers):
        #     if "uvicorn" in lgr.name:
        #         loggers.remove(lgr)
        #         print("deleting", lgr)

        self.install_signal_handlers()

        colored_message = f"Started server process [{t.cyan(str(process_id))}]"
        logger.info(colored_message)

        await self.startup_monitoring()
        await self.startup_server(sockets=sockets)
        await self.startup_db()

        if self.should_exit:
            return

        await self.main_loop()

        logger.info("Initiating application shutdown")
        await self.shutdown_feed_connection()
        await self.shutdown_server(sockets=sockets)

        color_message = f"Finished server process [{t.cyan(str(process_id))}]"
        logger.info(color_message)


    async def startup_server(self, sockets=None):
        await self.lifespan.startup()
        if self.lifespan.should_exit:
            self.should_exit = True
            return

        config = self.config

        create_protocol = functools.partial(
            config.http_protocol_class, config=config, server_state=self.server_state
        )

        loop = asyncio.get_event_loop()

        if sockets is not None:
            # Explicitly passed a list of open sockets.
            # We use this when the server is run from a Gunicorn worker.
            self.servers = []
            for sock in sockets:
                server = await loop.create_server(
                    create_protocol,
                    sock=sock,
                    ssl=config.ssl,
                    backlog=config.backlog
                )
                self.servers.append(server)

        elif config.fd is not None:
            # Use an existing socket, from a file descriptor.
            sock = socket.fromfd(config.fd, socket.AF_UNIX, socket.SOCK_STREAM)
            server = await loop.create_server(
                create_protocol, sock=sock, ssl=config.ssl, backlog=config.backlog
            )
            message = "Uvicorn running on socket %s (Press CTRL+C to quit)"
            logger.info(message % str(sock.getsockname()))
            self.servers = [server]

        elif config.uds is not None:
            # Create a socket using UNIX domain socket.
            uds_perms = 0o666
            if os.path.exists(config.uds):
                uds_perms = os.stat(config.uds).st_mode
            server = await loop.create_unix_server(
                create_protocol,
                path=config.uds,
                ssl=config.ssl,
                backlog=config.backlog
            )
            os.chmod(config.uds, uds_perms)
            message = "Uvicorn running on unix socket %s (Press CTRL+C to quit)"
            logger.info(message % config.uds)
            self.servers = [server]

        else:
            # Standard case. Create a socket from a host/port pair.
            try:
                server = await loop.create_server(
                    create_protocol,
                    host=config.host,
                    port=config.port,
                    ssl=config.ssl,
                    backlog=config.backlog,
                )
            except OSError as exc:
                logger.error(exc)
                await self.lifespan.shutdown()
                sys.exit(1)
            port = config.port
            if port == 0:
                port = server.sockets[0].getsockname()[1]
            protocol_name = "https" if config.ssl else "http"

            protoc = t.cyan(f"{protocol_name}://{config.host}:{port!r}")
            color_message = f"Uvicorn running on {protoc} (Press CTRL+C to quit)"
            logger.info(color_message)

            self.servers = [server]

        self.started = True
        # so we can use this instance in other modules
        settings.SERVER = self



    async def startup_monitoring(self):
        # start monit daemon
        startup_monit()
        self.heartbeat = Heartbeat(heartbeat_key="server", is_active=True)


    async def startup_db(self):
        await startup_exchange_table()
        await record_new_account_update(event="startup")
        await startup_strategy_table()



    async def setup_redis_sub(self):

        # aioredis pool connection to use across entire server module
        settings.AIOREDIS_POOL = await aioredis.create_redis_pool(('localhost', 6379))
        self.aioredis_pool = settings.AIOREDIS_POOL

        for key, channel_name in self.sub_map.items():
            subd_chan = await self.aioredis_pool.psubscribe(channel_name)
            # subscription always returns a list of channels
            self.subscribed_channels[key] = subd_chan[0]
            # self.redis_tasks.append(self.consume_from_channel(key, subd_chan[0]))
            if key == "public_orderbook_updates":
                self.redis_tasks.append(self.consume_public_orderbook(subd_chan[0]))
            if key == "public_trade_updates":
                self.redis_tasks.append(self.consume_public_trades(subd_chan[0]))
            if key == "public_spread_updates":
                self.redis_tasks.append(self.consume_public_spread(subd_chan[0]))
            if key == "public_instrument_updates":
                self.redis_tasks.append(self.consume_public_instrument(subd_chan[0]))
            if key == "private_trade_updates":
                self.redis_tasks.append(self.consume_user_trades(subd_chan[0]))
            if key == "private_order_updates":
                self.redis_tasks.append(self.consume_user_orders(subd_chan[0]))

        logger.debug(f"redis tasks : {self.redis_tasks}")
        logger.debug(f"subscribed channels : {self.subscribed_channels}")




    async def consume_public_orderbook(self, channel):
        async for _chan, message in channel.iter():
            if self.should_exit:
                break

            await update_public_orderbook(exchange="kraken", message=message)


    async def consume_public_trades(self, channel):
        async for _chan, message in channel.iter():
            if self.should_exit:
                break

            await update_public_trades(exchange="kraken", message=message)


    async def consume_public_spread(self, channel):
        async for _chan, message in channel.iter():
            if self.should_exit:
                break

            await update_public_spread(exchange="kraken", message=message)


    async def consume_public_instrument(self, channel):
        async for _chan, message in channel.iter():
            if self.should_exit:
                break

            await update_public_instrument(exchange="kraken", message=message)


    async def consume_user_trades(self, channel):
        async for _chan, message in channel.iter():
            if self.should_exit:
                break

            await update_user_trades(exchange="kraken", message=message)


    async def consume_user_orders(self, channel):
        async for _chan, message in channel.iter():
            if self.should_exit:
                break

            await update_user_orders(exchange="kraken", message=message)


    async def watcher(self):
        # if item gets appended to list of tasks, we create task and await it
        # when task is done, notify caller function
        # while True:
        #     if self.should_exit:
        #         break

        try:
            coro, kwargs = settings.SCHEDULED.popleft()
            print(coro, kwargs)
            if coro:
                print("watcher launching retrieved coro")
                task = asyncio.ensure_future(coro(**kwargs))
                # await coro(**kwargs)
        except IndexError:
            # continue
            pass
        except Exception as e:
            raise e





    async def main_loop(self, tick_interval=settings.TICK_INTERVAL):
        counter = 0
        should_exit = await self.on_tick(counter, tick_interval)
        while not should_exit:
            counter += 1

            # do we need to change 864000 to some other number ?
            counter = counter % 864000
            await asyncio.sleep(tick_interval)
            should_exit = await self.on_tick(counter, tick_interval)


    async def on_tick(self, counter, tick_interval) -> bool:
        # Update the default headers, once per second.
        if counter % (1/tick_interval) == 0:
            current_time = time.time()
            current_date = formatdate(current_time, usegmt=True).encode()
            self.server_state.default_headers = [
                (b"date", current_date)
            ] + self.config.encoded_headers

            # Callback to `callback_notify` once every `timeout_notify` seconds.
            if self.config.callback_notify is not None:
                if current_time - self.last_notified > self.config.timeout_notify:
                    self.last_notified = current_time
                    await self.config.callback_notify()

            # heartbeat once per second
            self.heartbeat.beat()

            # check if we have scheduled tasks once per second
            await self.watcher() #!

        # Write balance to db every minute
        if counter % (60/tick_interval) == 0:
            # await record_new_balance_update(event="periodic")
            await record_new_account_update(event="periodic")

            # holding = await self.aioredis_pool.get(f"db:balance:holdings:kraken")
            # logger.info(f"Holdings : {ujson.loads(holding)}")
            # positions = await self.aioredis_pool.get(f"db:balance:positions:kraken")
            # logger.info(f"Positions : {ujson.loads(positions)}")
            # account_value = await self.aioredis_pool.get(f"db:balance:account_value:kraken")
            # logger.info(f"Account value : {ujson.loads(account_value)}")



        # Determine if we should exit.
        if self.should_exit:
            return True
        if self.config.limit_max_requests is not None:
            return self.server_state.total_requests >= self.config.limit_max_requests
        return False



    async def shutdown_server(self, sockets=None):

        # Stop accepting new connections.
        for socket in sockets or []:
            socket.close()
        for server in self.servers:
            server.close()
        for server in self.servers:
            await server.wait_closed()

        # Request shutdown on all existing connections.
        for connection in list(self.server_state.connections):
            connection.shutdown()
        await asyncio.sleep(0.1)

        # Wait for existing connections to finish sending responses.
        if self.server_state.connections and not self.force_exit:
            msg = "Waiting for connections to close. (CTRL+C to force quit)"
            logger.info(msg)
            while self.server_state.connections and not self.force_exit:
                await asyncio.sleep(0.1)

        # Wait for existing tasks to complete.
        if self.server_state.tasks and not self.force_exit:
            msg = "Waiting for background tasks to complete. (CTRL+C to force quit)"
            logger.info(msg)
            while self.server_state.tasks and not self.force_exit:
                await asyncio.sleep(0.1)

        # Send the lifespan shutdown event, and wait for application shutdown.
        if not self.force_exit:
            await self.lifespan.shutdown()


    async def shutdown_feed_connection(self):
        self.aioredis_pool.close()
        await self.aioredis_pool.wait_closed()



    def install_signal_handlers(self):
        loop = asyncio.get_event_loop()

        try:
            for sig in HANDLED_SIGNALS:
                loop.add_signal_handler(sig, self.handle_exit, sig, None)
        except NotImplementedError as exc:
            # Windows
            for sig in HANDLED_SIGNALS:
                signal.signal(sig, self.handle_exit)


    def handle_exit(self, sig, frame):
        if self.should_exit:
            self.force_exit = True
        else:
            self.should_exit = True
