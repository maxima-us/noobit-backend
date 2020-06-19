from typing import List
import asyncio
import os

import uvloop
from tortoise import Tortoise

from noobit.logger.structlogger import get_logger, log_exception
from noobit.engine.base import BaseStrategy
import noobit_user

logger = get_logger(__name__)

class StratRunner():

    """
    We would like to run it like this :

    strat1 = Strategy(exchange="kraken", pair="xbt-usd", timeframe=240, volume=20, indicators=[talib.MAMA])
    strat2 = Strategy(exchange="kraken", pair="eth-usd", timeframe=120, volume=15, indicators=[talib.MAMA])
    strat3 = Strategy(exchange="kraken", pair="link-usd", timeframe=60, volume=5, indicators=[talib.MAMA])

    runner = StratRunner(strats=[strat1, strat2, strat3])
    runner.run()
    """


    def __init__(self, strats: List[BaseStrategy]):
        """
        strats is a list of strategy instances subclassing BaseStrategy
        """
        self.strats = strats
        self.tasks = []


    async def init_tortoise(self):
        # Here we create a SQLite DB using file "db.sqlite3"
        #  also specify the app name of "models"
        #  which contain models from "app.models"
        user_dir = noobit_user.get_abs_path()
        await Tortoise.init(db_url=f"sqlite://{user_dir}/data/fastapi.db",
                            modules={"models": ["noobit.models.orm"]},
                            )
        # Generate the schema
        await Tortoise.generate_schemas()


    async def shutdown_tortoise(self):
        await Tortoise.close_connections()


    async def setup_strats(self):
        for strat in self.strats:
            try:
                await strat.register_to_db()
                await strat.subscribe_to_ws()

                logger.debug(strat.ws)
                logger.debug(strat.ws_token)
                logger.info(f"Strategy : {strat.name} --- Running")
                logger.info(f"Arguments : {strat.exchange} - {strat.symbol} - {strat.timeframe}")

            except Exception as e:
                log_exception(logger, e)

            if strat.execution_models:
                for _key, model in strat.execution_models.items():
                    try:
                        await model.setup()
                        self.tasks.extend(model.redis_tasks)

                        logger.debug(model.ws)
                        logger.debug(model.ws_token)

                    except Exception as e:
                        log_exception(logger, e)

            self.tasks.append(strat.main_loop())


    def shutdown_strats(self):
        for strat in self.strats:
            strat.should_exit = True
            for _key, model in strat.execution_models.items():
                model.should_exit = True


    async def main(self):
        results = await asyncio.gather(*self.tasks)
        return results


    def run(self):

        process_id = os.getpid()
        logger.info(f"Starting process {process_id}")

        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.init_tortoise())
            loop.run_until_complete(self.setup_strats())
        except Exception as e:
            log_exception(logger, e)

        try:
            loop.run_until_complete(self.main())

        except KeyboardInterrupt:
            self.shutdown_strats()
            print("Keyboard Interrupt")

        finally:
            loop = asyncio.get_event_loop()
            tasks = asyncio.all_tasks(loop)

            logger.info("Initiating shutdown")
            for task in tasks:
                task.cancel()
                try:
                    loop.run_until_complete(task)
                except asyncio.CancelledError:
                    logger.info(f'{task} is now cancelled')

            logger.info("Closing Db connections")
            loop.run_until_complete(self.shutdown_tortoise())

            logger.info("Stopping Event Loop")
            loop.stop()
            logger.info("Closing Event Loop")
            loop.close()
