import json
import logging
from collections import Counter

import ujson
import aioredis
import stackprinter

from server import settings
from models.orm_models.strategy import Strategy
from models.orm_models.exchange import Exchange
from exchanges.mappings import rest_api_map
from exchanges.base.rest.api import BaseRestAPI


async def startup_strategy():

    try:
        strategies = await Strategy.all().values()
        # returns a list of dicts of the format {id: int , holdings:{}, exchange_id: int}

        # if Balance table is empty:
        if not strategies:
            logging.warning(f"Strategy : db table is empty")

            try:
                await Strategy.create(
                    id=0,
                    name="discretionary",
                    type="discrionary"
                )

            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))

        
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))