"""Kraken Rest API
"""
import urllib
import hashlib
import base64
import hmac
import os
import asyncio
from decimal import Decimal
from collections import deque
from typing import Optional
from typing_extensions import Literal

import logging
import stackprinter
import requests
from dotenv import load_dotenv

from noobit.server import settings
# import noobit.models.data.response.parse.kraken as parse_resp
# import noobit.models.data.request.parse.kraken as parse_req
from noobit.models.data.response.parse.kraken import KrakenResponseParser
from noobit.models.data.request.parse.kraken import KrakenRequestParser
from .endpoints_map import mapping
from ...base.rest import BaseRestAPI

load_dotenv()


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

        self.exchange = "Kraken"
        self.base_url = mapping[self.exchange]["base_url"]
        self.public_endpoint = mapping[self.exchange]["public_endpoint"]
        self.private_endpoint = mapping[self.exchange]["private_endpoint"]
        self.public_methods = mapping[self.exchange]["public_methods"]
        self.private_methods = mapping[self.exchange]["private_methods"]

        #  this block can be set in the base class
        # self._load_all_env_keys()
        # self.to_standard_format = self._load_normalize_map()
        # self.to_exchange_format = {v:k for k, v in self.to_standard_format.items()}
        # self.exchange_pair_specs = self._load_pair_specs_map()
        # self.session = settings.SESSION
        # self.response = None
        # self._json_options = {}
        # settings.SYMBOL_MAP_TO_EXCHANGE[self.exchange.upper()] = self.to_exchange_format
        # settings.SYMBOL_MAP_TO_STANDARD[self.exchange.upper()] = self.to_standard_format

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
            logging.error(stackprinter.format(e, style="darkbg2"))



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
            We can't use query public because it will cause a recursion error
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



    async def _handle_response_errors(self, response):
        # dict is empty
        if not response:
            logging.error("Response|Error: Value is None")
            return {"accept": True, "value": None}

        # response returns error message
        # valid means wether or not we accept the response as is or we want to retry
        if response["error"]:

            if response["error"] == ['EOrder:Insufficient funds']:
                logging.error("Response|Error: Insufficent funds to place order")
                return {"accept": True, "value": None}

            elif response["error"] in [["EService:Unavailable"], ["EService:Busy"]]:
                logging.error("Response|Error: Exchange unavailable")
                await asyncio.sleep(60)
                return {"accept": False, "value": None}

            elif response["error"] == ["EGeneral:Temporary lockout"]:
                logging.error("Response|Error: Locked out")
                await asyncio.sleep(60)
                return {"accept": False, "value": None}

            elif response["error"] == ["EAPI:Rate limit exceeded"]:
                logging.error("Response|Error: Rate Limit Exceeded")
                return {"accept": True, "value": None}

            elif response["error"] == ["EGeneral:Invalid arguments"]:
                logging.error(f"Response|Error: Invalid arguments")
                return {"accept": True, "value": None}

            else:
                try:
                    logging.error(f"Error with request : {response['error']}\n{12*' '}Request URL : {self.response.url}\n{12*' '}With data : {self.response.data}")
                except Exception as e:
                    logging.error(stackprinter.format(e, style="darkbg2"))

        else:
            return {"accept": True, "value": response["result"]}




    # ================================================================================
    # ==== USER API QUERIES


    # ================================================================================
    # ====== PUBLIC REQUESTS
    # ================================================================================


    async def get_mapping(self) -> dict:
        """Mapping of exchange format asset or pairs to standardized format asset or pairs.
        """
        return self.to_standard_format




    # ================================================================================
    # ====== PRIVATE REQUESTS
    # ================================================================================


    # async def get_order(self,
    #                     mode: Literal["to_list", "by_id"],
    #                     orderID: str,
    #                     clOrdID: Optional[int] = None,
    #                     retries: int = 1
    #                     ):
    #     """Get a single order
    #         mode (str): Parse response to list or index by order id
    #         orderID: ID of the order to query (ID as assigned by broker)
    #         clOrdID (str): Restrict results to given ID
    #     """
    #     data = parse_req.order(mode, orderID, clOrdID)

    #     response = await self.query_private(method="order_info", data=data, retries=retries)
    #     # parse to order response model and validate
    #     parsed_response = parse_resp.order_response(response=response, mode=mode)

    #     return parsed_response




    # async def get_open_orders(self,
    #                           mode: Literal["to_list", "by_id"],
    #                           symbol: Optional[str] = None,
    #                           clOrdID: Optional[int] = None,
    #                           retries: int = 1
    #                           ):
    #     """Get open orders.

    #     Args:
    #         mode (str): Parse response to list or index by order id
    #         symbol (str): Instrument symbol
    #         clOrdID (str): Restrict results to given ID

    #     Returns:
    #         open orders
    #     """

    #     data = parse_req.open_orders(mode, symbol, clOrdID)

    #     response = await self.query_private(method="open_orders", data=data, retries=retries)
    #     # parse to order response model and validate
    #     parsed_response = parse_resp.order_response(response=response, mode=mode)

    #     return parsed_response




    # async def get_closed_orders(self,
    #                             mode: Literal["to_list", "by_id"],
    #                             symbol: Optional[str] = None,
    #                             clOrdID: Optional[int] = None,
    #                             retries: int = 1
    #                             ):
    #     """Get closed orders.

    #     Args:
    #         symbol (str): Instrument symbol
    #         clOrdID (str): Restrict results to given ID
    #         mode (str): Parse response to list or index by order id

    #     Returns:
    #         closed orders
    #     """

    #     data = parse_req.closed_orders(mode, symbol, clOrdID)

    #     response = await self.query_private(method="closed_orders", data=data, retries=retries)
    #     # parse to order response model and validate
    #     parsed_response = parse_resp.order_response(response=response, mode=mode)

    #     return parsed_response




    # ================================================================================
    # ====== PRIVATE USER TRADING
    # ================================================================================
    #! We should make sure to update cache and database every time we use these


    async def place_order(self,
                          pair: list,
                          side: str,
                          ordertype: str,
                          volume: float,
                          price: float = None,
                          price2: float = None,
                          leverage: int = None,
                          start_time: int = None,
                          expire_time: int = None,
                          userref: int = None,
                          validate: bool = False,
                          oflags: list = None,
                          retries: int = 0
                          ):
        """Place an order.

        Args:
            pair = asset pair
            side = type of order (buy/sell)
            ordertype = order type:
                market
                limit (price = limit price)
                stop-loss (price = stop loss price)
                take-profit (price = take profit price)
                stop-loss-profit (price = stop loss price, price2 = take profit price)
                stop-loss-profit-limit (price = stop loss price, price2 = take profit price)
                stop-loss-limit (price = stop loss trigger price, price2 = triggered limit price)
                take-profit-limit (price = take profit trigger price, price2 = triggered limit price)
                trailing-stop (price = trailing stop offset)
                trailing-stop-limit (price = trailing stop offset, price2 = triggered limit offset)
                stop-loss-and-limit (price = stop loss price, price2 = limit price)
                settle-position
            volume = order volume in lots
            price = price (optional. dependent on ordertype)
            price2 = secondary price (optional. dependent on ordertype)
            leverage = amount of leverage desired (optional.  default = none)
            oflags = comma delimited list of order flags (optional):
                viqc = volume in quote currency (not available for leveraged orders)
                fcib = prefer fee in base currency
                fciq = prefer fee in quote currency
                nompp = no market price protection
                post = post only order (available when ordertype = limit)
            start_time = scheduled start time (optional):
                0 = now (default)
                +<n> = schedule start time <n> seconds from now
                <n> = unix timestamp of start time
            expire_time = expiration time (optional):
                0 = no expiration (default)
                +<n> = expire <n> seconds from now
                <n> = unix timestamp of expiration time
            userref = user reference id.  32-bit signed number.  (optional)
            validate = validate inputs only.  do not submit order (optional)

            optional closing order to add to system when order gets filled:
                close[ordertype] = order type
                close[price] = price
                close[price2] = secondary price

        Returns:
            descr = order description info
                order = order description
                close = conditional close order description (if conditional close set)
            txid = array of transaction ids for order (if order was added successfully)
        """
        pair = pair[0].upper()

        try:
            price_decimals = Decimal(self.exchange_pair_specs[pair]["price_decimals"])
            price = Decimal(price).quantize(10**-price_decimals)

            if price2:
                price2 = Decimal(price2).quantize(10**-price_decimals)

            volume_decimals = Decimal(self.exchange_pair_specs[pair]["volume_decimals"])
            volume = Decimal(volume).quantize(10**-volume_decimals)

        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))


        data = {
            "pair": pair,
            "type": side,
            "ordertype": ordertype,
            "price": price,
            "price2": price2,
            "volume": volume,
            "leverage": leverage,
            "oflags": oflags,
            "starttm": start_time,
            "expiretm": expire_time,
            "userref": userref,
            "validate": validate
        }

        msg = f"price decimals : {self.exchange_pair_specs[pair]['price_decimals']}"
        logging.info(msg)

        response = await self.query_private(method="place_order",
                                            data=data,
                                            retries=retries
                                            )

        return response



    async def cancel_order(self, txid: str, retries: int = 0):
        """Cancel an Open Order.

        Args:
            txid (str): transaction id

        Returns:
            count : number of orders canceled
            pending : if set, order(s) is/are pending cancellation
        """
        data = {"txid": txid}
        response = await self.query_private(method="cancel_order",
                                            data=data,
                                            retries=retries
                                            )
        return response




    # ==== Websocket Auth Token
    # ========================================


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
        response = await self.query_private(method="ws_token",
                                            data=data,
                                            retries=retries
                                            )
        return response
