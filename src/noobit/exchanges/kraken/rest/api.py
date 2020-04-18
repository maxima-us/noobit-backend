"""Kraken Rest API
"""
import urllib
import hashlib
import base64
import hmac
import os
import asyncio
from collections import deque

import logging
import stackprinter
import requests
from dotenv import load_dotenv

from noobit.server import settings
from .endpoints_map import mapping
from ...base.rest.api import BaseRestAPI

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

    env_keys_dq = deque()

    def __init__(self):

        self.exchange = "Kraken"
        self.base_url = mapping[self.exchange]["base_url"]
        self.public_endpoint = mapping[self.exchange]["public_endpoint"]
        self.private_endpoint = mapping[self.exchange]["private_endpoint"]
        self.public_methods = mapping[self.exchange]["public_methods"]
        self.private_methods = mapping[self.exchange]["private_methods"]
        self.session = settings.SESSION #! should be in cache
        self.response = None
        self._json_options = {}


        self._load_all_env_keys()
        self.to_standard_format = self._load_normalize_map()
        self.to_exchange_format = {v:k for k, v in self.to_standard_format.items()}
        self.exchange_pair_specs = self._load_pair_specs_map()




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


    def _cleanup_input_data(self, data: dict):
        """Helper method to clean the dictionary we will pass as request payload.
        (Remove zero or None values, normalize pair/currency names)

        Args:
            data (dict): api request payload
        """

        if data is None:
            data = {}

        # input that needs to be passed in as comma delimited list:
        # pair, txid, asset
        else:

            # Store for later as we can not delete key during iteration
            invalid_keys = []

            for key in data.keys():

                # Convert to valid string
                if isinstance(data[key], bool):
                    data[key] = str(data[key]).lower()

                # Skip if value is None or [] or {} BUT don't skip if 0
                if (data[key] == []) or (data[key] == {}) or (data[key] is None):
                    invalid_keys.append(key)
                    logging.info(f"Passed empty value for : {key}")
                    continue

                elif key in ["asset", "pair", "txid"]:
                    # invalid_keys.append(key) => we don't have to delete the keys but instead edit them
                    logging.debug("Key = asset|pair|txid : Updating data dict to accomodate Kraken Api Format")

                    # in case we forgot to pass a list
                    if not isinstance(data[key], list):
                        data[key] = [data[key]]
                        logging.info("Please pass single pair as a list")


                    # convert normalized pair to exchange format / data["pair"] is a list
                    if key == "pair":
                        kraken_pairs = []
                        for pair in data[key]:
                            kraken_pairs.append(self.to_exchange_format[pair.upper()])

                        data[key] = kraken_pairs

                    # if we passed more than 1 element we need to change the value for given key
                    # edit : even for a single element, otherwise will throw error
                    if len(data[key]) > 0:
                        comma_list = ",".join(data[key])
                        # full_path = f"{full_path}?{key}={comma_list}"
                        data[key] = comma_list


            # we set these keys to the url => delete from data dict to not pass twice
            for key in invalid_keys:
                del data[key]

        return data



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

        pair_map = {k:v["wsname"].replace("/", "-") for k, v in response["result"].items() if ".d" not in k}

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
        Map standard format pairs to their specs (decima places of price and volume as well as available leverage)
        Needed to check if we do not pass incorrect values when placing orders
        """
        response = self._request_kraken_asset_pairs()

        pair_specs = {
            v["wsname"].replace("/", "-"): {
                "volume_decimals": v["lot_decimals"],
                "price_decimals": v["pair_decimals"],
                "leverage_available": v["leverage_sell"]
            }
            for k, v in response["result"].items() if ".d" not in k}

        return pair_specs



    def _normalize_response(self, response: str):
        # if not resp["error"]:
        #     fiat_list = ["usd", "USD", "eur", "EUR"]
        #     return {self.to_standard_format[k]:v for k,v in resp["result"].items() if any(fiat in k for fiat in fiat_list)}
        for k, v in self.to_standard_format.items():
            if k in response:
                response = response.replace(k, v)

        return response



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



    async def get_raw_ticker(self, pair: list, retries: int = 0) -> dict:
        """Raw (unchecked) ticker data for given pair.

        Args:
            pair (list) : list of requested pairs
                input format : ["XBT-USD", "ETH-USD"]
                must be passed as list even if single pair
            retries (int): number of request retry attempts

        Returns:
            dict that must follow Ticker data model

        """

        payload = {"pair": pair}
        response = await self.query_public(method="ticker",
                                           data=payload,
                                           retries=retries
                                           )
        # response will be of format :
        # {"XETHZUSD":{"a":["239.64000","29","29.000"],"b":["239.52000","2","2.000"],"c":["240.00000","1.86852042"],
        #              "v":["33879.87184540","76436.35260966"],"p":["234.32426","232.54493"],"t":[4043,7989],
        #              "l":["227.67000","226.72000"],"h":["241.80000","241.80000"],"o":"228.64000"},

        #  "XXBTZUSD":{"a":["9134.10000","1","1.000"],"b":["9133.10000","2","2.000"],"c":["9134.10000","0.01200000"],
        #              "v":["1572.18277937","3951.32636727"],"p":["9094.01315","9095.67807"],"t":[4995,12404],
        #              "l":["9001.90000","9001.90000"],"h":["9175.00000","9175.00000"],"o":"9066.00000"}
        #  }

        remap = {"a": "ask",
                 "b": "bid",
                 "c": "close",
                 "v": "volume",
                 "p": "vwap",
                 "t": "trades",
                 "l": "low",
                 "h": "high",
                 "o": "open"
                 }

        remap_response = {}

        for pair, v_dict in response.items():
            remap_response[pair] = {remap[k]:v for k, v in v_dict.items()}

        return remap_response



    async def get_raw_ohlc(self, pair: list, timeframe: int, since: int = None, retries=0) -> dict:
        """Raw OHLC data (not checked against our data models).

        Args:
            pair (list) : list containing single request pair
            timeframe (int) : candle timeframe in minutes
                possible values : 1 (default), 5, 15, 30, 60, 240, 1440, 10080, 21600
            since : return committed OHLC data since given id (optional)
            retries (int): number of request retry attempts


        Returns:
            dict : 2 keys
                "data" must follow data_models.Ohlc.data model
                "last" must follow data_models.Ohlc.last model
        """

        data = {"pair" : pair, "interval": timeframe, "since": since}
        response = await self.query_public(method="ohlc",
                                           data=data,
                                           retries=retries
                                           )
        # response will be of format :
        # {"XXBTZUSD":[
        #               [1580925600,"9559.1","9765.0","9559.1","9678.3","9662.3","1294.49384347",3639],
        #               ......
        #               [1583514000,"9069.1","9082.5","9069.0","9078.0","9074.8","24.33633768",88]
        #              ],
        # "last":1583510400
        # }

        try:
            data = response[pair[0].upper()]
            last = response["last"]
        except Exception as e:
            logging.error(stackprinter.format(e, style='darkbg2'))

        return {"data": data, "last": last}



    async def get_raw_orderbook(self, pair: list, count: int = None, retries: int = 0) -> dict:
        """Raw Orderbook data (not checked against our data models).

        Args:
            pair (list) : asset pair to get market depth for
            count (int) : maximum number of asks/bids (optional)
            retries (int): number of request retry attempts

        Returns:
            dict : 2 keys
                "ask": array of <price>, <volume>, <timestamp>
                "bids": array of <price>, <volume>, <timestamp>
        """

        data = {"pair": pair, "count": count}
        response = await self.query_public(method="orderbook",
                                           data=data,
                                           retries=retries
                                           )

        # response is of format:
        # {"XXBTZUSD":{"asks":[["9108.50000","3.309",1583527816],
        #                       ...........
        #                      ["9155.00000","6.000",1583527437]],
        #              "bids":[["9107.60000","0.024",1583527808],
        #                       ...........
        #                      ["9054.00000","1.000",1583523232]]
        #              }
        # }

        try:
            asks = response[pair[0].upper()]["asks"]
            bids = response[pair[0].upper()]["bids"]
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

        return {"asks": asks, "bids": bids}


    async def get_raw_trades(self, pair: list, since: int = None, retries: int = 0) -> dict:
        """Raw trades data (not validated against data model).

        Args:
            pair (list): asset pair to get trade data for
            since (int): return trade data since given id (optional.  exclusive)

        Returns:
            dict : 2 keys
                data : array of <price>, <volume>, <timestamp>
                last : array of <price>, <volume>, <timestamp>
        """

        data = {"pair": pair, "since": since}
        # we should use the private endpoint since this will mainly be used to
        # aggregate historical trade data, so we dont get rate limited as easily
        response = await self.query_public(method="trades",
                                           data=data,
                                           retries=retries
                                           )
        # response is of format :
        # {"XXBTZUSD":[
        #               ["8862.70000","0.96511005",1583604462.0163,"b","l",""],
        #               ................
        #               ["8895.20000","0.10000000",1583610370.7438,"b","m",""]
        #              ],
        # "last":"1583610370743780877"}

        try:
            data = response[pair[0].upper()]
            last = response["last"]
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

        return {"data": data, "last": last}


    async def get_raw_spread(self, pair: list, since: int = None, retries: int = 0) -> dict:
        """Raw spread data (not validated against data model).

        Args:
            retries (int):
            pair (list): asset pair to get spread data for
            since (int): return spread data since given id (optional.  inclusive)

        Returns:
            dict : keys
                data (list) : array of entries <time>, <bid>, <ask>
                last (Decimal) : id to be used as since when polling for new data
        """

        data = {"pair": pair, "since": since}
        response = await self.query_public(method="spread",
                                           data=data,
                                           retries=retries
                                           )
        # response is of format :
        # {"XXBTZUSD":[
        #              [1583610484,"8887.90000","8889.60000"],
        #               ................
        #              [1583610677,"8886.40000","8886.50000"]
        #             ],
        # "last":1583610677}

        try:
            data = response[pair[0].upper()]
            last = response["last"]
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

        return {"data": data, "last": last}




    # ================================================================================
    # ====== PRIVATE REQUESTS
    # ================================================================================


    async def get_raw_account_balance(self, retries: int = 0) -> dict:
        """Raw account balance (not validated against data model).

        Args:
            retries (int)

        Returns:
            dictionary : format
                <asset name> : <balance amount>
        """

        response = await self.query_private(method="account_balance", retries=retries)
        # response returns a dict with of format {asset name : balance}

        nz_balances = {k:v for k, v in response.items() if float(v) > 0}

        # return non_zero
        return nz_balances


    async def get_raw_trade_balance(self, asset_class: str = None, asset: str = None, retries: int = 0) -> dict:
        """Raw trade balance data (not validated against data model).

        Args:
            asset_class (str): asset class (optional):
                currency (default)
            asset (str): base asset used to determine balance (default = ZUSD)

        Returns:
            dict

        Notes:
            Response returns a dict with following keys:
            eb = equivalent balance (combined balance of all currencies)
            tb = trade balance (combined balance of all equity currencies)
            m = margin amount of open positions
            n = unrealized net profit/loss of open positions
            c = cost basis of open positions
            v = current floating valuation of open positions
            e = equity = trade balance + unrealized net profit/loss
            mf = free margin = equity - initial margin (maximum margin available to open new positions)
            ml = margin level = (equity / initial margin) * 100

        Note:
            I dont't really understand what is meant by asset_class input in the API Docs
        """

        data = {"asset": asset}
        response = await self.query_private(method="trade_balance",
                                            data=data,
                                            retries=retries
                                            )

        #   for model validation we need "ml" key to have a value
        #   response dict might not contain "ml" key if no positions are open
        if not response.get("ml"):
            response["ml"] = 0

        remap = {"eb": "equivalent_balance",
                 "tb": "trade_balance",
                 "m": "positions_margin",
                 "n": "positions_unrealized",
                 "c": "positions_cost",
                 "v": "positions_valuation",
                 "e": "equity",
                 "mf": "free_margin",
                 "ml": "margin_level"
                }

        return {remap[k]:v for k, v in response.items()}


    async def get_raw_open_orders(self, userref: int = None, trades: bool = True, retries: int = 0) -> dict:
        """Raw ropen orders (not validated against data model).

        Args:
            trades (bool): whether or not to include trades in output (optional.  default = false)
            userref (int): restrict results to given user reference id (optional)
            retries

        Returns:
            data : dict of order info in open array with txid as the key

            refid = Referral order transaction id that created this order
            userref = user reference id
            status = status of order:
                pending = order pending book entry
                open = open order
                closed = closed order
                canceled = order canceled
                expired = order expired
            opentm = unix timestamp of when order was placed
            starttm = unix timestamp of order start time (or 0 if not set)
            expiretm = unix timestamp of order end time (or 0 if not set)
            descr = order description info
                pair = asset pair
                type = type of order (buy/sell)
                ordertype = order type (See Add standard order)
                price = primary price
                price2 = secondary price
                leverage = amount of leverage
                order = order description
                close = conditional close order description (if conditional close set)
            vol = volume of order (base currency unless viqc set in oflags)
            vol_exec = volume executed (base currency unless viqc set in oflags)
            cost = total cost (quote currency unless unless viqc set in oflags)
            fee = total fee (quote currency)
            price = average price (quote currency unless viqc set in oflags)
            stopprice = stop price (quote currency, for trailing stops)
            limitprice = triggered limit price (quote currency, when limit based order type triggered)
            misc = comma delimited list of miscellaneous info
                stopped = triggered by stop price
                touched = triggered by touch price
                liquidated = liquidation
                partial = partial fill
            oflags = comma delimited list of order flags
                viqc = volume in quote currency
                fcib = prefer fee in base currency (default if selling)
                fciq = prefer fee in quote currency (default if buying)
                nompp = no market price protection
            trades = array of trade ids related to order (if trades info requested and data available)

        Note:
            What is userref ?
            Absolutely not sure how to handle trades arg, need to be passed as true in url
            == For now we don't pass any data

        Todo:
            descr row is still a dict, need to flatten
        """

        data = {"userref": userref, "trades": trades}
        response = await self.query_private(method="open_orders",
                                            data=data,
                                            retries=retries
                                            )

        # df = pd.DataFrame.from_dict(response["open"], orient="index") # ==> better to orient along index
        # return df
        return response["open"]


    async def get_raw_closed_orders(self, offset: int = 0,
                                    trades: bool = False,
                                    userref: int = None,
                                    start: int = None,
                                    end: int = None,
                                    closetime: str = "both",
                                    retries: int = 0
                                    ) -> dict:
        """Closed orders data.

        Args:
            trades (bool): whether or not to include trades in output (optional.  default = false)
            userref (int): restrict results to given user reference id (optional)
            start (int): starting unix timestamp or order tx id of results (optional.  exclusive)
            end (int): ending unix timestamp or order tx id of results (optional.  inclusive)
            offset (int): result offset
            closetime (str): which time to use (optional)
                open
                close
                both (default)

        Returns:
            data : dict of order info in closed array with txid as the key

            refid = Referral order transaction id that created this order
            userref = user reference id
            status = status of order:
                pending = order pending book entry
                open = open order
                closed = closed order
                canceled = order canceled
                expired = order expired
            opentm = unix timestamp of when order was placed
            starttm = unix timestamp of order start time (or 0 if not set)
            expiretm = unix timestamp of order end time (or 0 if not set)
            descr = order description info
                pair = asset pair
                type = type of order (buy/sell)
                ordertype = order type (See Add standard order)
                price = primary price
                price2 = secondary price
                leverage = amount of leverage
                order = order description
                close = conditional close order description (if conditional close set)
            vol = volume of order (base currency unless viqc set in oflags)
            vol_exec = volume executed (base currency unless viqc set in oflags)
            cost = total cost (quote currency unless unless viqc set in oflags)
            fee = total fee (quote currency)
            price = average price (quote currency unless viqc set in oflags)
            stopprice = stop price (quote currency, for trailing stops)
            limitprice = triggered limit price (quote currency, when limit based order type triggered)
            misc = comma delimited list of miscellaneous info
                stopped = triggered by stop price
                touched = triggered by touch price
                liquidated = liquidation
                partial = partial fill
            oflags = comma delimited list of order flags
                viqc = volume in quote currency
                fcib = prefer fee in base currency (default if selling)
                fciq = prefer fee in quote currency (default if buying)
                nompp = no market price protection
            trades = array of trade ids related to order (if trades info requested and data available)
            closetm = unix timestamp of when order was closed
            reason = additional info on status (if any)

        Note:
            What is userref
            Absolutely not sure how to handle trades/start/end/closetime args
            What should start/end default to ?
            How do we pass a java string for closetime ?
            == For now we don't pass any data
        """

        data = {"ofs": offset, "trades": trades, "userref": userref, "start": start, "end": end, "closetime": closetime}
        response = await self.query_private(method="closed_orders",
                                            data=data,
                                            retries=retries
                                            )

        # df = pd.DataFrame.from_dict(response["closed"], orient="index") # ==> better to orient along index
        # return df
        return response["closed"]

    async def get_raw_user_trades(self, trade_type: str = "all",
                                  trades: bool = False,
                                  start: int = None,
                                  end: int = None,
                                  retries: int = 0
                                  ) -> dict:
        """User's historical trades.

        Args:
            trade_type (str): type of trade (optional)
                all = all types (default)
                any position = any position (open or closed)
                closed position = positions that have been closed
                closing position = any trade closing all or part of a position
                no position = non-positional trades
            trades (bool): whether or not to include trades related to position in output (optional.  default = false)
            start (int): starting unix timestamp or trade tx id of results (optional.  exclusive)
            end (int): ending unix timestamp or trade tx id of results (optional.  inclusive)
            !!!!!!!!! ofs = result offset ==> we didnt include this, should we?

        Returns:
            pandas.DataFrame
            index :
            columns :
            ordertxid = order responsible for execution of trade
            pair = asset pair
            time = unix timestamp of trade (in seconds)
            type = type of order (buy/sell)
            ordertype = order type
            price = average price order was executed at (quote currency)
            cost = total cost of order (quote currency)
            fee = total fee (quote currency)
            vol = volume (base currency)
            margin = initial margin (quote currency)
            misc = comma delimited list of miscellaneous info
                closing = trade closes all or part of a position

        Notes
            Trades (bool) not passed to data dict
        """

        data = {"type": trade_type, "start": start, "end": end, "trades": trades}
        response = await self.query_private(method="trades_history",
                                            data=data,
                                            retries=retries
                                            )

        # df = pd.DataFrame.from_dict(response["trades"], orient="index")
        # return df       # we don't want to return "count" value as we can get it from df
        return response["trades"]


    async def get_raw_open_positions(self, txid: list = None, show_pnl: bool = True, retries: int = 0) -> dict:
        """Open positions data.

        Args:
            txid (list):
            show_pnl (bool):
            retries (int):

        Returns:
            pandas.DataFrame
            index : ordertxid
            columns :
            pair = asset pair
            time = unix timestamp of trade
            type = type of order used to open position (buy/sell)
            ordertype = order type used to open position
            cost = opening cost of position (quote currency unless viqc set in oflags)
            fee = opening fee of position (quote currency)
            vol = position volume (base currency unless viqc set in oflags)
            vol_closed = position volume closed (base currency unless viqc set in oflags)
            margin = initial margin (quote currency)
            value = current value of remaining position (if docalcs requested.  quote currency)
            net = unrealized profit/loss of remaining position (if docalcs requested.  quote currency, quote currency scale)
            misc = comma delimited list of miscellaneous info
            oflags = comma delimited list of order flags
                viqc = volume in quote currency
        """


        data = {"txid": txid, "docalcs": show_pnl}
        response = await self.query_private(method="open_positions",
                                            data=data,
                                            retries=retries
                                            )

        # df = pd.DataFrame.from_dict(response, orient="index")
        # return df
        return response


    async def get_raw_order_info(self, txid: str, trades: bool = True, userref: int = None, retries: int = 0):
        """
        Result: dict of {ordertxid : orders info}
        """
        data = {"txid": [txid], "trades": trades, "userref": userref}
        response = await self.query_private(method="order_info",
                                            data=data,
                                            retries=retries
                                            )
        return response[txid]




    # ==== Private User Trading
    # ========================================
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
