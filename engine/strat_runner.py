from typing import List
import asyncio
import os

import uvloop
from tortoise import Tortoise

from engine.strategy import BaseStrategy

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
        await Tortoise.init(db_url="sqlite://fastapi.db",
                            modules={"models": ["models.orm_models"]},
                            )
        # Generate the schema
        await Tortoise.generate_schemas()


    async def shutdown_tortoise(self):
        await Tortoise.close_connections()


    async def setup_strats(self):
        for strat in self.strats:
            await strat.register()
            # start task telling strat to run
            self.tasks.append(strat.main_loop())

    def shutdown_strats(self):
        for strat in self.strats:
            strat.should_exit = True


    async def main(self):
        results = await asyncio.gather(*self.tasks)
        return results


    def run(self):

        process_id = os.getpid()
        print(f"Starting process {process_id}")

        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.init_tortoise())
        loop.run_until_complete(self.setup_strats())


        try:
            loop.run_until_complete(self.main())



        except KeyboardInterrupt:
            self.shutdown_strats()
            print("Keyboard Interrupt")


        finally:
            loop = asyncio.get_event_loop()
            tasks = asyncio.all_tasks(loop)
            print("Initiating shutdown")
            for task in tasks:
                task.cancel()
            print("Closing Db connections")
            loop.run_until_complete(self.shutdown_tortoise())
            print("Stopping Event Loop")
            loop.stop()
            print("Closing Event Loop")
            loop.close()
