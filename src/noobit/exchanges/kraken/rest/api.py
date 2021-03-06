"""New Format of our exchange Rest API

No query methods are defined here, instead we just define them abstractely in the base class
and define response and request parsers in noobit.models.data
"""
import urllib
import hashlib
import base64
import hmac
import os
import asyncio
from collections import deque

import requests
from dotenv import load_dotenv
from starlette import status
import pandas as pd

from noobit_user import get_abs_path

# logger
from noobit.logger.structlogger import (get_logger, log_exc_to_db, log_exception)

# base classes
from noobit.exchanges.base.rest import BaseRestAPI

# models
from noobit.models.data.base.types import PAIR
from noobit.models.data.base.response import OKResponse, ErrorResponse

# parsers
from noobit.models.data.response.parse.kraken import KrakenResponseParser
from noobit.models.data.request.parse.kraken import KrakenRequestParser

# mappings
from .endpoints_map import mapping

load_dotenv()

logger = get_logger(__name__)
# derived from krakenex https://github.com/veox/python3-krakenex/blob/master/krakenex/api.py


class KrakenRestAPI(BaseRestAPI):
    """Maintains a single session between this machine and Kraken.
    Specifying a key/secret pair is optional. If not specified, private
    queries will not be possible.
    The :py:attr:`session` attribute is a :py:class:`requests.Session`
    object. Customise networking options by manipulating it.
    Query responses, as received by :py:mod:`requests`, are retained
    as attribute :py:attr:`response` of this object. It is overwritten
    on each query.
    .. note::
       No query rate limiting is performed.
    """

    # env_keys_dq = deque()

    def __init__(self):

        #! SETTLE FOR A FORMAT FOR ALL PAIRS AND EXCHANGE NAMES
        #! Maybe it is better to capitalize everything  since most exchanges seem to want capital pairs
        self.exchange = "Kraken"
        self.base_url = mapping[self.exchange]["base_url"]
        self.public_endpoint = mapping[self.exchange]["public_endpoint"]
        self.private_endpoint = mapping[self.exchange]["private_endpoint"]
        self.public_methods = mapping[self.exchange]["public_methods"]
        self.private_methods = mapping[self.exchange]["private_methods"]


        self.response_parser = KrakenResponseParser()
        self.request_parser = KrakenRequestParser()

        super().__init__()



    # ================================================================================
    # ==== AUTHENTICATION
    # ================================================================================


    def _load_all_env_keys(self):
        """Loads all keys from env file into cls.env_keys_dq

        Notes:
            In .env file, keys should contain :
                API Key : <exchange-name> & "key"
                API Secret : <exchange-name> & "secret"
        """
        try:
            env_list_of_tuples = []
            env_dict = list(dict(os.environ).items())
            for k, v in env_dict:
                if self.exchange.upper() in k:
                    if "KEY" in k:
                        tuple_api_key = v
                        env_secret_key = k.replace("KEY", "SECRET")
                        tuple_secret_key = os.environ[env_secret_key]
                        env_list_of_tuples.append((tuple_api_key, tuple_secret_key))

            self._set_class_var(deque(env_list_of_tuples, maxlen=len(env_list_of_tuples)))

        except Exception as e:
            log_exception(logger, e)



    def _sign(self, data: dict, urlpath: str):
        """Sign request data according to Kraken's scheme.

        Args:
            data (dict): API request parameters
            urlpath (str): API URL path sans host

        Returns
            signature digest
        """
        postdata = urllib.parse.urlencode(data)

        # Unicode-objects must be encoded before hashing
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        signature = hmac.new(base64.b64decode(self.current_secret()),
                             message,
                             hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())

        return sigdigest.decode()




    # ================================================================================
    # ==== UTILS
    # ================================================================================



    def _request_kraken_asset_pairs(self):
        base_url = mapping[self.exchange]["base_url"]
        public_endpoint = mapping[self.exchange]["public_endpoint"]
        method_endpoint = mapping[self.exchange]["public_methods"]["tradable_pairs"]
        response = requests.get(f"{base_url}{public_endpoint}/{method_endpoint}")
        response = response.json()

        return response



    def _load_normalize_map(self):
        """Map kraken format assets or pair to standardized format assets or pair.

        Returns:
            dict of format :
                {<XXBTZUSD>:<XBT-USD>, <XXBT>:<XBT>}

        Note:
            We can't use query_public method because it will cause a recursion error so we use the requests module
        """
        response = self._request_kraken_asset_pairs()
        # {XXBTZUSD: XBT-USD}
        pair_map = {k:v["wsname"].replace("/", "-") for k, v in response["result"].items() if ".d" not in k}
        # {XBTUSD: XBT-USD}
        pair_map_2 = {v["altname"]:v["wsname"].replace("/", "-") for k, v in response["result"].items() if ".d" not in k}
        pair_map.update(pair_map_2)

        # {XXBT: XBT, ZUSD: USD}
        asset_map = {}
        for k, v in response["result"].items():
            if ".d" not in k:
                kraken_format_base = v["base"]
                kraken_format_quote = v["quote"]
                stand_format_base, stand_format_quote = v["wsname"].split("/")
                asset_map[kraken_format_base] = stand_format_base
                asset_map[kraken_format_quote] = stand_format_quote

        pair_map.update(asset_map)

        return pair_map



    def _load_pair_specs_map(self):
        """
        Map standard format pairs to their specs (decimal places of price and volume as well as available leverage)
        Needed to check if we do not pass incorrect values when placing orders
        """
        response = self._request_kraken_asset_pairs()

        pair_specs = {
            v["wsname"].replace("/", "-"): {
                "volume_decimals": (v["lot_decimals"]),
                "price_decimals": (v["pair_decimals"]),
                "leverage_available": (v["leverage_sell"])
            }
            for k, v in response["result"].items() if ".d" not in k}

        return pair_specs



    async def get_mapping(self) -> dict:
        """Mapping of exchange format asset or pairs to standardized format asset or pairs.
        """
        return self.to_standard_format




    # ================================================================================
    # ==== WEBSOCKET AUTH TOKEN
    # ================================================================================



    async def get_websocket_auth_token(self, validity: int = None, permissions: list = None, retries: int = 0):
        """Get auth token to subscribe to private websocket feed.

        Args:
            validity (int) : number of minutes that token is valid
                (optional / default (max): 60 minutes)
            permissions (list) : comma separated list of allowed feeds
                (optional / default: all)

        Returns:
            dict
            keys:
            token (str) : token to authenticate private websocket subscription
            expires (int) : time to expiry

        Note:

            The API client must request an authentication "token" via the following REST API endpoint "GetWebSocketsToken"
            to connect to WebSockets Private endpoints.
            The token should be used within 15 minutes of creation.
            The token does not expire once a connection to a WebSockets API private message (openOrders or ownTrades) is maintained.


        This should be called at startup, we get a token, then subscribe to a ws feed
        We receive all the updates for our orders and send it to redis
        That way we can track position changes almost at tick speed without needing to make rest calls
        We will need to check the token creation time on every tick and a get new token every 30/40 minutes
        """

        data = {"validity": validity, "permissions": permissions}
        result = await self.query_private(method="ws_token",
                                            data=data,
                                            retries=retries
                                            )
        if result.is_ok:
            return OKResponse(
                status_code=status.HTTP_200_OK,
                value=result.value
            )
        else:
            return ErrorResponse(
                status_code=result.status_code,
                value=result.value
            )




    # ================================================================================
    # ==== AGGREGATE HISTRICAL TRADES IF THERE IS NO DIRECT ENDPOINT
    # ================================================================================

    async def aggregate_historical_trades(self, symbol: PAIR):
        """
        kraken does not provide historical ohlc data
        ==> aggregate all historical trades into ohlc

        Note:
            So far this is very slow, since we use the get_public_trades method from the API.
            The method is public and Krakens rate limits are very low for public requests.
            Eventually, change this to make an authenticated requests.
        """
        noobit_user_path = get_abs_path()
        file_path = f"{noobit_user_path}/data/{self.exchange.lower()}_{symbol}_historical_trade_data_fix_api.csv"

        # init
        since = 0
        count = 0

        parsed_response = await self.get_public_trades(symbol=symbol)
        most_recent_trades = parsed_response.value["data"]
        most_recent_last = parsed_response.value["last"]

        # verify data validity
        try:
            df = pd.read_csv(file_path,
                             names=[
                                 "symbol",
                                 "side",
                                 "ordType",
                                 "avgPx",
                                 "cumQty",
                                 "grossTradeAmt",
                                 "transactTime",
                             ],
                            #  header=None,
                            #  skiprows=1
                             )
            logger.info(df.tail(10))

            # get index for row with highest timestamp
            max_ts = df["transactTime"].max()
            logger.info(f"most recent timestamp:  {max_ts}")

            [max_ts_index] = df.index[df["transactTime"] == max_ts].tolist()
            logger.info(f"corresponding index: {max_ts_index}")
            # drop row where index > max_ts_index
            # (means they were wrongly appended to file)
            df = df[(df["transactTime"] <= max_ts) & (df.index <= max_ts_index)]

            # overwrite
            df.to_csv(path_or_buf=file_path,
                      mode="w",
                      header=False,
                      index=False,
                      )

            since = df["transactTime"].iloc[-1]
            logger.info(df.tail(10))
            logger.info(f"Datetime of last Trade entry: {pd.to_datetime(since)}")

        except FileNotFoundError as e:
            logger.warning("CSV file does not exist")
            logger.warning("Creating file and populating with latest trades data")
            since_0_trades = await self.get_public_trades(symbol, since=0)
            trades_df = pd.DataFrame(since_0_trades.value["data"])
            trades_df = trades_df.drop(
                [
                    "trdMatchID",
                    "orderID",
                    "clOrdID",
                    "commission",
                    "tickDirection",
                    "text"
                ],
                axis=1
            )
            trades_df.to_csv(path_or_buf=file_path,
                             mode="w",
                             header=False,
                             index=False,
                             )

        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)



        try:
            while since < most_recent_last:
                #! get_public_trades has no since arg yet, need to add it
                trades = await self.get_public_trades(symbol=symbol, since=since)
                #! now returns data under a different format
                trades_df = pd.DataFrame(trades.value["data"])
                trades_df = trades_df.drop(
                    [
                        "trdMatchID",
                        "orderID",
                        "clOrdID",
                        "commission",
                        "tickDirection",
                        "text"
                    ],
                    axis=1
                )
                trades_df.to_csv(path_or_buf=file_path,
                                 mode="a",
                                 header=False,
                                 index=False,
                                 )
                count += len(trades.value["data"])
                since = trades.value["last"]
                # otherwise we will get rate limited
                await asyncio.sleep(2)
                logger.info(f"count : {count}")
                logger.info(pd.to_datetime(int(since)))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)

        return {"count": count}
