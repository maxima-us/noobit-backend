'''
Hack uvicorn main file to launch our own service on top of it
'''
import asyncio
import functools
import logging
import os
import platform
import signal
import socket
import sys
import time
from email.utils import formatdate

import click

import uvicorn
from uvicorn.config import (
    HTTP_PROTOCOLS,
    INTERFACES,
    LIFESPAN,
    LOG_LEVELS,
    LOGGING_CONFIG,
    LOOP_SETUPS,
    SSL_PROTOCOL_VERSION,
    WS_PROTOCOLS,
    Config,
)
from uvicorn.supervisors import Multiprocess, StatReload

LEVEL_CHOICES = click.Choice(LOG_LEVELS.keys())
HTTP_CHOICES = click.Choice(HTTP_PROTOCOLS.keys())
WS_CHOICES = click.Choice(WS_PROTOCOLS.keys())
LIFESPAN_CHOICES = click.Choice(LIFESPAN.keys())
LOOP_CHOICES = click.Choice([key for key in LOOP_SETUPS.keys() if key != "none"])
INTERFACE_CHOICES = click.Choice(INTERFACES)

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


# =====================================================================================
# =====================================================================================
# from structlogger import get_logger
# logger = get_logger(__name__)



# =================== Setup Stackprinter ======================= #
import stackprinter
stackprinter.set_excepthook(style='darkbg2')


# =================== Set logger ======================= #

# configure_logger("uvicorn.error")
logger = logging.getLogger("uvicorn.error")

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
# added import necessary for bot


import ujson
import aioredis
from server import settings
from server.db_utils.balance import startup_balance_table, record_new_balance_update
from server.db_utils.strategy import startup_strategy_table
from server.db_utils.update_from_ws import update_user_trades, update_user_orders, update_public_trades, update_public_spread
from server.startup.monit import startup_monit
from server.monitor.heartbeat import Heartbeat



def run(app, **kwargs):

    config = Config(app, **kwargs)
    config.backlog = 2048           #! for some reason we need to specify this
    server = Server(config=config)

    if (config.reload or config.workers > 1) and not isinstance(app, str):
        logger = logging.getLogger("uvicorn.error")
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

        # attributes necessary for strat
        self.target_api = None
        self.cache = None
        self.strat = None
        self.strat_tf_value = None
        self.strat_tf_unit = None

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
            self.sub_map = {"heartbeat": "ws:heartbeat:*",
                            "status": "ws:status:*",
                            "system": "ws:system:*",
                            "user_order_updates": "ws:private:data:update:kraken:openOrders",
                            "user_trade_updates": "ws:private:data:update:kraken:ownTrades",
                            "public_trade_updates": "ws:public:data:update:kraken:trade:*",
                            "public_ticker_updates": "ws:pubic:data:update:kraken:ticker",
                            "public_spread_updates": "ws:public:data:update:kraken:spread:xbt-usd"
                            }
        else:
            self.sub_map = sub_map


    #! this is the part we need to replace in backend.main
    def run(self, sockets=None):
        self.config.setup_event_loop()
        loop = asyncio.get_event_loop()
        # loop.run_until_complete(self.startup_feed_consumer())
        # loop.run_until_complete(self.serve(sockets=sockets))
        loop.run_until_complete(self.main(sockets))

        # try:
        #     loop.run_until_complete(self.main(sockets))
        # except KeyboardInterrupt:
        #     self.should_exit = True
        #     print("Keyboard Interrupt")
        # finally:
        #     loop = asyncio.get_event_loop()
        #     tasks = asyncio.all_tasks(loop)
        #     print(f"Closing tasks : {asyncio.current_task(loop)}")
        #     for task in tasks:
        #         task.cancel()
        #     print("Initiating shutdown")
        #     loop.run_until_complete(self.shutdown_server())
        #     print("Stopping Event Loop")
        #     loop.stop()
        #     print("Closing Event Loop")
        #     loop.close()


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

        self.install_signal_handlers()

        message = "Started server process [%d]"
        color_message = "Started server process [" + click.style("%d", fg="cyan") + "]"
        logger.info(message, process_id, extra={"color_message": color_message})

        await self.startup_monitoring()
        await self.startup_server(sockets=sockets)
        await self.startup_db()

        if self.should_exit:
            return

        await self.main_loop()

        logger.info("Initiating application shutdown")
        await self.shutdown_feed_connection()
        await self.shutdown_server(sockets=sockets)


        message = "Finished server process [%d]"
        color_message = "Finished server process [" + click.style("%d", fg="cyan") + "]"
        logger.info(
            "Finished server process [%d]",
            process_id,
            extra={"color_message": color_message},
        )



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
            message = "Uvicorn running on %s://%s:%d (Press CTRL+C to quit)"
            color_message = (
                "Uvicorn running on "
                + click.style("%s://%s:%d", bold=True)
                + " (Press CTRL+C to quit)"
            )
            logger.info(
                message,
                protocol_name,
                config.host,
                port,
                extra={"color_message": color_message},
            )
            self.servers = [server]

        self.started = True
        # so we can use this instance in other modules
        settings.SERVER = self



    async def startup_monitoring(self):
        # start monit daemon
        startup_monit()
        self.heartbeat = Heartbeat(heartbeat_key="server", is_active=True)


    async def startup_db(self):
        await startup_balance_table()
        await record_new_balance_update(event="startup")
        await startup_strategy_table()



    async def setup_redis_sub(self):
        # self.open_websockets["private"] = await connect_private_websockets(api=self.target_api)
        # self.open_websockets["public"] = await connect_public_websockets(pairs=["XBT/USD"])

        # ==> We will read websocket data from redis sub
        # self.private_ws = KrakenPrivateFeedReader(api=self.target_api)
        # con_status = await self.private_ws.connect_to_ws()
        # sub_status = await self.private_ws.subscribe()
        # aioredis pool connection to use across entire server module
        settings.AIOREDIS_POOL = await aioredis.create_redis_pool('redis://localhost')
        self.aioredis_pool = settings.AIOREDIS_POOL

        for key, channel_name in self.sub_map.items():
            subd_chan = await self.aioredis_pool.psubscribe(channel_name)
            # subscription always returns a list
            self.subscribed_channels[key] = subd_chan[0]
            self.redis_tasks.append(self.consume_from_channel(key, subd_chan[0]))

        logger.debug(f"redis tasks : {self.redis_tasks}")
        logger.debug(f"subscribed channels : {self.subscribed_channels}")


    async def consume_from_channel(self, key, channel):
        async for _chan, message in channel.iter():
            if self.should_exit:
                break

            # decide what we do with each message
            # ==> if its a private trade or order we need to write to db

            if key == "public_trade_updates":
                await update_public_trades(exchange="kraken", message=message)

            if key == "user_trade_updates":
                # update trades db table
                await update_user_trades(exchange="kraken", message=message)
                # TODO update balance db table (remove or add the bought/sold asset)
                #       take into account trade fees
                # TODO update cache with new balance

            if key == "user_order_updates":
                await update_user_orders(exchange="kraken", message=message)
                # TODO push new order to cache ?

            if key == "public_spread_updates":
                await update_public_spread(exchange="kraken", message=message)



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

        # Write balance to db every minute
        if counter % (60/tick_interval) == 0:
            await record_new_balance_update(event="periodic")

            holding = await self.aioredis_pool.get(f"db:balance:holdings:kraken")
            logger.info(f"Holdings : {ujson.loads(holding)}")
            positions = await self.aioredis_pool.get(f"db:balance:positions:kraken")
            logger.info(f"Positions : {ujson.loads(positions)}")
            account_value = await self.aioredis_pool.get(f"db:balance:account_value:kraken")
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

        #   ! no ws anymore
        # logger.info("Closing Websockets")
        # for _, ws in self.open_websockets.items():
        #     await ws.close()

        self.aioredis_pool.close()
        await self.aioredis_pool.wait_closed()

        #! Check balances at shutdown
        # logger.info("Updating Balances")
        # await shutdown_balances()




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
