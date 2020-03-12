import logging
import stackprinter
import talib

from server import settings

# this should import api abstract baseclass in the future
from exchanges.kraken.rest.api import KrakenRestAPI
from exchanges.kraken.utils.clean_data import ohlc_to_pandas, open_orders_flattened, flatten_response_dict


async def on_schedule(api: KrakenRestAPI):
    '''
    pass in Api instance we instantiated and cached at startup according to the target exchange 
    we are given in our settings file (should later become an env file) 
    '''

    try:
        # TODO  write helper function to get the interval from settings automatically

        ticker = await api.get_open_positions()
        logging.info(ticker)


    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))