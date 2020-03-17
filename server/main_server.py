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
import ssl
import sys
import time
import datetime
import typing
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
import websockets
import aioredis
from server import settings                                    
from server.startup.balance import startup_balances
from server.shutdown.balance import shutdown_balances
from server.startup.monit import startup_monit
from server.monitor.heartbeat import Heartbeat
from .redis_sub import FeedConsumer

# this needs to be replaced
from exchanges.mappings import rest_api_map



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
    def __init__(self, config):
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
        self.open_websockets = {}
        self.private_ws = None
        self.public_ws = None
        self.redis_sub = None


    #! this is the part we need to replace in backend.main
    def run(self, sockets=None):
        self.config.setup_event_loop()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.serve(sockets=sockets))


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

        await self.startup(sockets=sockets)
        if self.should_exit:
            return
        await self.main_loop()
        await self.shutdown(sockets=sockets)


        message = "Finished server process [%d]"
        color_message = "Finished server process [" + click.style("%d", fg="cyan") + "]"
        logger.info(
            "Finished server process [%d]",
            process_id,
            extra={"color_message": color_message},
        )


    async def startup(self, sockets=None):
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


        # TODO put all of this in a start_trading_bot file ==> maybe put in serve func above instead of here
        # start monit daemon
        startup_monit()

        #! change variables name to remain consistent across app
        self.cache = settings.REDIS
        # self.target_exchange = self.cache["target_exchange"]
        # self.target_api = rest_api_map[self.target_exchange]()

        self.heartbeat = Heartbeat(heartbeat_key="server", is_active=True)


        await startup_balances(redis_instance=self.cache)
        # self.open_websockets["private"] = await connect_private_websockets(api=self.target_api)
        # self.open_websockets["public"] = await connect_public_websockets(pairs=["XBT/USD"])


        # ==> We will read websocket data from redis sub
        # self.private_ws = KrakenPrivateFeedReader(api=self.target_api)
        # con_status = await self.private_ws.connect_to_ws()
        # sub_status = await self.private_ws.subscribe()

        self.redis_sub = FeedConsumer()
        await self.redis_sub.subscribe()


        #! also check balances at shutdown

        self.started = True


    async def main_loop(self, tick_interval=settings.TICK_INTERVAL):
        counter = 0
        should_exit = await self.on_tick(counter, tick_interval)
        while not should_exit:
            counter += 1

            # do we need to change 864000 to some other number ?
            counter = counter % 864000
            await asyncio.sleep(tick_interval)
            should_exit = await self.on_tick(counter, tick_interval)




    # ================================================================================
    # ======== TICK LOGIC THAT WE REMOVE TO PLACE IN ENGINE MODULE
    # ================================================================================


    # async def pre_algo_tick(self):
    #     '''
    #     Pre algo tick we should : \t
    #     - check balances to be able to manage risk ==> from cache \t
    #     - check open orders ==> from cache \t
    #     - check profit so we can lock in some if we want ==> probably thru WS price updates \t
    #     - send a bool to continue (or not) with on_algo_tick ? \t
    #     - track open order status ==> which orders have been filled/how much ?
    #     '''

    #     logging.info("---- pre tick ----")
        
    #     # msgs = await self.open_websockets["public"].recv()


    #     # try :
    #     #     for feed in self.private_ws.feeds:
    #     #         msgs = await self.private_ws.read_feed(feed)
    #     #         events = await self.private_ws.read_feed("events")
    #     #         logging.info(f"messages : {msgs}")
    #     #         logging.info(f"events : {events}")

    #     # except Exception as e:
    #     #     logging.error(stackprinter.format(e, style="darkbg2"))

    #     try:
    #         #!  this is very slow somehow, figure out where bottleneck is
    #         #!  we should probably rewrite the whole websocket file so that it is started
    #         #!      as a separate process that sends all the data to redis 
    #         #!      pre_algo then just reads data from redis
    #         await self.private_ws.read_feed("openOrders")
    #         # logging.info(msgs)
    #         # await aiologger.info(f"messages: {msgs}")
    #     except Exception as e:
    #         logging.error(stackprinter.format(e, style="darkbg2"))

    #     # TODO  Parse messages from ownTrades and openOrders
    #     # TODO  Update trades and orders table accordingly
    #     # TODO   


    # async def on_algo_tick(self, hour, minute, second, microsecond):
    #     '''
    #     On algo tick we should: \t
    #     - determine which strat is run \b \t
    #     - determine what timeframe we want \b \t
    #     - determine what datetimes will be our checkpoints \b \t
    #     - at each checkpoint, fetch data \b \t
    #     - at each checkpoint, run strat logic on the fetched data to see what we do \b \t
    #     - make sure our orders were executed \t
    #     - update database and cache if we did anything \t

    #     also check out from gryphon: \t
    #     - heartbeat (touch file on each tick) \t
    #     - monit \t

    #     !!! 
    #     We should also implement sthg in case we want to adjust our orders dynamically
    #     For example if we want to limit chase, or if we have a MM strategy
    #     How would we keep adjusting our order continuously ?
    #     For this our on_schedule fonction would need to talk to this loop, so that we know
    #         we need to keep track of this order and execute some logic until it is filled

    #     Concrete example : 
    #     on a 4H EMA cross, our on_schedule func wants to buy 1 BTC, but limit chasing up the price
    #     sends data to cache : buy 1 btc  
    #     sends data to cache : execution_algo = limit_chase_up 
    #     set execution to True
    #     on each algo tick : check cache, if order is still there : execute given execution algo
    #                                      if some of it was eaten : update cache and execute
    #                                      if filled : delete cache data for given order
    #                                                  set execution to False

    #     ==> we will need to feed the execution algo with websocket orderbook data
    #     ==> on schedule will basically just be the trigger to launch execution algo

    #     '''


    #     # Run strat function if we are at a checkpoint

    #     allowed_units = ["hour", "minute"]
    #     sub_tf_condition = (minute == 0 and second == 0 and microsecond<10**5) if self.strat_tf_unit == "hour" else (second == 0 and microsecond<10**5)

    #     if self.strat_tf_unit in allowed_units:
    #         try:
    #             if eval(self.strat_tf_unit) % self.strat_tf_value == 0 and sub_tf_condition:
    #                 try:
    #                     # await asyncio.wait_for(self.strat.on_schedule(self.target_api), timeout=1)
    #                     await self.strat.on_schedule(self.target_api)
    #                 except Exception as e:
    #                     logging.warning(f"Algo Tick function timed out :{str(e)}")
    #                 logging.info(f"UTC-{hour}-{minute}-{second}-{microsecond} : algo running ")

    #         except Exception as e:
    #             logging.error(stackprinter.format(e, style="darkbg2"))
    #     else:
    #         logging.warning("Invalid Strategy Interval")
    #         pass




    # ================================================================================
    # ================================================================================

        
    async def on_tick(self, counter, tick_interval) -> bool:

        # await self.pre_algo_tick()
        
        # # come up with sthg smarter, like instantiating our counter given time at startup ? 
        # dt = datetime.datetime.utcnow()

        # await self.on_algo_tick(hour=dt.hour, 
        #                         minute=dt.minute,
        #                         second=dt.second,
        #                         microsecond=dt.microsecond
        #                         )
        
        #consume ws messages
        # await self.redis_sub.consume_from_channel(self.redis_sub.subd_channels["status"])
        # await self.redis_sub.consume_from_channel(self.redis_sub.subd_channels["events"])
        # await self.redis_sub.consume_from_channel(self.redis_sub.subd_channels["data"])
        # await self.redis_sub.consume_from_channel(self.redis_sub.subd_channels["system"])
        # trades_update = await self.redis_sub.consume_from_channel(self.redis_sub.subd_channels["kraken_orders"])
        # if trades_update:
        #     print(ujson.loads(trades_update))


        await self.redis_sub.update_orders(exchange="kraken")


        # Update the default headers, once per second.
        if counter % (1/tick_interval) == 0:
            # logging.info(f"One second gone, tick interval is : {tick_interval}")                     #added
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


        # Determine if we should exit.
        if self.should_exit:
            return True
        if self.config.limit_max_requests is not None:
            return self.server_state.total_requests >= self.config.limit_max_requests
        return False


    async def shutdown(self, sockets=None):
        logger.warning("Initiating application shutdown.")
        
        logger.info("Closing Websockets")
        for _, ws in self.open_websockets.items():
            await ws.close()

        #! Check balances at shutdown
        logger.info("Updating Balances")
        await shutdown_balances()

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

