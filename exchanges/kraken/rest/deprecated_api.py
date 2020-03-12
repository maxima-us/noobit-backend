from server import settings

import urllib
import hashlib
import base64
import hmac
import time
import os
from functools import wraps
from collections import namedtuple, deque 
import json

import logging
import stackprinter

from dotenv import load_dotenv
load_dotenv()

import pandas as pd

from .endpoints_map import mapping
from ..utils.pairs import normalize_currency, normalize_pair, kraken_format_pair
from ..utils.clean_data import flatten_response_dict, balance_remove_zero_values
from ...base.rest.api import BaseRestAPI



''' from krakenex https://github.com/veox/python3-krakenex/blob/master/krakenex/api.py '''
# !!!!! this should subclass an abstract base class and only define speficic methods


class KrakenRestAPI(BaseRestAPI):
    """ Maintains a single session between this machine and Kraken.
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
        """ Create an object with authentication information.  
        :param key: (optional) key identifier for queries to the API  
        :type key: str   
        :param secret: (optional) actual private key used to sign messages  
        :type secret: str  
        :returns: None  
        """


        self.exchange = "Kraken"
        self.base_url = mapping[self.exchange]["base_url"]
        self.public_endpoint = mapping[self.exchange]["public_endpoint"]
        self.private_endpoint = mapping[self.exchange]["private_endpoint"]
        self.session = settings.SESSION #! should be in cache
        self.response = None
        self._json_options = {}

        self._load_all_env_keys()

        return


    def json_options(self, **kwargs):
        """ Set keyword arguments to be passed to JSON deserialization.
        :param kwargs: passed to :py:meth:`requests.Response.json`
        :returns: this instance for chaining
        """
        self._json_options = kwargs
        return self


    async def close(self):
        """ close this session.
        :returns: none
        """
        await self.session.aclose()
        return




    # ================================================================================
    # ================================================================================
    # ==== AUTHENTICATION


    # def _load_env(self, key):
    #     return str(os.environ[key])


    # def load_creds(self):
    #     try:
    #         self.key = self._load_env('KRAKEN_API_KEY')
    #         self.secret = self._load_env('KRAKEN_API_SECRET')
    #     except Exception as e:
    #         logging.error(stackprinter.format(e, style="darkbg2"))

    def _load_all_env_keys(self):
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


    @classmethod
    def _set_class_var(cls, value):
        if not cls.env_keys_dq:
            cls.env_keys_dq = value


    @classmethod
    def _rotate_api_keys(cls):
        try:
            cls.env_keys_dq.rotate(-1)
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))


    def current_key(self):
        return self.env_keys_dq[0][0]

    
    def current_secret(self):
        return self.env_keys_dq[0][1]

    # def load_key(self, path):
    #     """ Load key and secret from env.
    #     :returns: None
    #     """
    #     with open(path, 'r') as f:
    #         self.key = f.readline().strip()
    #         self.secret = f.readline().strip()
    #     return
    
    
    def _nonce(self):
        """ Nonce counter.
        :returns: an always-increasing unsigned integer (up to 64 bits wide)
        """
        return int(1000*time.time())


    def _sign(self, data, urlpath):
        """ Sign request data according to Kraken's scheme.
        :param data: API request parameters  
        :type data: dict  
        :param urlpath: API URL path sans host  
        :type urlpath: str   
        :returns: signature digest  
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
    # ================================================================================
    # ==== BASE API QUERIES


    async def retry(self, *, func: object, retry_attempts: int=0, **kwargs):
        attempts = 0
        while True:
            try:
                r = await func(**kwargs)
                return r
            except Exception as e:
                attempts += 1
                if attempts > retry_attempts:
                    raise e
                else:
                    logging.warning(u'[RETRY REQUEST] - This time failed.  Trying Again.')
                    time.sleep(0.1)


    def cleanup_data_dict(self, data: dict):
        """Helper method to clean the dictionary we will pass as request payload\t
        (Remove zero or None values, normalize pair/currency names)
        """
        
        if data is None:
            data = {}

        # input that needs to be passed in as comma delimited list:
        # pair, txid, asset
        else : 
            if "asset" in data.keys():
                pass
                # convert normalized asset to exchange format
                # if data["asset"].lower() in ["usd", "eur"]:
                #     kraken_asset = f"Z{data['asset'].upper()}"

                # else:
                #     kraken_asset = f"Z{data['asset'].upper()}"
                
                # data["asset"] = kraken_asset


            # Store for later as we can not delete key during iteration
            invalid_keys = []
            
            for key in data.keys():

                # Convert to valid string
                if data[key] == True|False:
                    data[key] = str(data[key]).lower()
                
                # Skip if value is None or [] or {}
                if (not data[key]) or (data[key] is None):
                    invalid_keys.append(key)
                    logging.warning(f"Passed empty value for : {key}")
                    continue


                elif key in ["asset", "pair", "txid"]:
                    # invalid_keys.append(key) => we don't have to delete the keys but instead edit them
                    logging.warning("Key = asset|pair|txid : Updating data dict to accomodate Kraken Api Format")

                    # in case we forgot to pass a list
                    if not isinstance(data[key], list):
                        data[key] = [data[key]]
                        logging.warning("Please pass single pair as a list")


                    # convert normalized pair to exchange format / data["pair"] is a list
                    if key == "pair":
                        kraken_pairs = []
                        for pair in data[key]:
                            kraken_pairs.append(kraken_format_pair(pair))
                    
                        data[key] = kraken_pairs
                    
                    # if we passed more than 1 element we need to change the value for given key
                    # edit : even for a single element, otherwise will throw error
                    if len(data[key])>0:
                        comma_list = ",".join(data[key])
                        # full_path = f"{full_path}?{key}={comma_list}"
                        data[key] = comma_list


            # we set these keys to the url => delete from data dict to not pass twice
            for key in invalid_keys:
                del data[key]

        return data 


    async def _query(self, endpoint, data: dict, private: bool, headers=None, timeout=None, json=None, retries=0):
        """ Low-level query handling.
        .. note::
           Use :py:meth:`query_private` or :py:meth:`query_public`
           unless you have a good reason not to.
        :param endpoint: API URL path sans host
        :type endpoint: str
        :param data: API request parameters
        :type data: dict
        :param headers: (optional) HTTPS headers
        :type headers: dict
        :param timeout: (optional) if not ``None``, a :py:exc:`requests.HTTPError`
                        will be thrown after ``timeout`` seconds if a response
                        has not been received
        :type timeout: int or float
        :returns: :py:meth:`requests.Response.json`-deserialised Python object
        :raises: :py:exc:`requests.HTTPError`: if response status not successful
        """

        full_path = f"{self.base_url}{endpoint}"

        if headers is None:
            headers = {}

        #KRAKEN Docs :
        #Public methods can use either GET or POST.
        #Private methods must use POST and be set up as follows [...]

        if private:
            self.response = await self.retry(func = self.session.post,
                                            url = full_path, 
                                            data = data, 
                                            json = json,
                                            headers = headers,
                                            timeout = timeout,
                                            retry_attempts=retries
                                            )
    
        else:
            self.response = await self.retry(func = self.session.get,
                                            url = full_path,
                                            params = data,
                                            timeout = timeout,
                                            retry_attempts = retries
                                            )

        if self.response.status_code not in (200, 201, 202):
            self.response.raise_for_status()

        logging.debug(f"API Request for url : {self.response.url}")

        return self.response.json(**self._json_options)


    async def query_public(self, method, data=None, timeout=None, retries=0):
        """ Performs an API query that does not require a valid key/secret pair.

        Args:
            method (str) : method key as defined in endpoints map
            data (dict) : (optional) API request parameters
                pair value should be passed as a list
            timeout (float) : (optional) 
                if not ``None``, throw Error after ``timeout`` seconds if no response
        
        Returns:
            response.json (dict) : deserialised Python object
        """
        
        data = self.cleanup_data_dict(data)

        method_endpoint = mapping[self.exchange]["public_methods"][method] 
        method_path = f"{self.public_endpoint}/{method_endpoint}"

        #! should we handle response["error"] here ?
        req = await self._query(endpoint=method_path, 
                                data=data, 
                                private=False, 
                                timeout=timeout, 
                                retries=retries
                                )


        if req["error"]:
            logging.warning(f"Error with public request : {req['error']}\n{12*' '}Request URL : {self.response.url}\n{12*' '}With data : {data}")
            #! if error is : ['EGeneral:Temporary lockout'] we need to wait 
            return
        result_normalize_pairs = {(normalize_pair(k) if (len(k)>7 and k[0]=="X" and k[4]=="Z") else k):v for k,v in req["result"].items()}
        return result_normalize_pairs
        

    async def query_private(self, method, data=None, timeout=None, retries=0):
        """ Performs an API query that requires a valid key/secret pair.
        :param method: API method name
        :type method: str
        :param data: (optional) API request parameters
        :type data: dict
        :param timeout: (optional) if not ``None``, a :py:exc:`requests.HTTPError`
                        will be thrown after ``timeout`` seconds if a response
                        has not been received
        :type timeout: int or float
        :returns: :py:meth:`requests.Response.json`-deserialised Python object
        """

        if not self.current_key() or not self.current_secret():
            raise Exception('Either key or secret is not set! (Use `load_key()`.')

        data = self.cleanup_data_dict(data)
        data['nonce'] = self._nonce()

        method_endpoint = mapping[self.exchange]["private_methods"][method]
        method_path = f"{self.private_endpoint}/{method_endpoint}"

        # headers = {
        #     'API-Key': self.key,
        #     'API-Sign': self._sign(data, method_path)
        # }

        headers = {
            'API-Key': self.current_key(),
            'API-Sign': self._sign(data, method_path)
        }

        req = await self._query(endpoint=method_path, 
                                data=data, 
                                json=json,
                                headers=headers, 
                                private=True, 
                                timeout=timeout, 
                                retries=retries
                                )

        self._rotate_api_keys()
        logging.debug(self.current_key())
        logging.debug(self.current_secret())

        if not req:
            logging.error("Response returned None")
        if req["error"]:
            logging.warning(f"Error with private request : {req['error']}\n{12*' '}Request URL : {self.response.url}\n{12*' '}With data : {data}")
            logging.warning(f"Error with private request :\n{12*' '}Key : {self.current_key()}\n{12*' '}Secret : {self.current_secret()}\n{12*' '}")
            #! if error is : ['EGeneral:Temporary lockout'] we need to wait 
            if req["error"] == ['EOrder:Insufficient funds']:
                logging.warning("Insufficent funds to place order")
            return
        result_normalize_pairs = {(normalize_pair(k) if (len(k)>7 and k[0]=="X" and k[4]=="Z") else k):v for k,v in req["result"].items()}
        return result_normalize_pairs 




    # ================================================================================
    # ================================================================================
    # ==== USER API QUERIES


    # ====== Public Methods
    # ========================================


    async def get_ticker(self, pair: list, retries: int=0) -> pd.DataFrame:
        """Returns ticker data for given pair

        Args:
            pair (list) : list of requested pairs
                input format : ["XBT-USD", "ETH-USD"]
                must be passed as list even if single pair
            retries (int): number of request retry attempts
    
        Returns:
            pandas.DataFrame : 
                index : pair
                columns :
                ask = ask array(<price>, <whole lot volume>, <lot volume>)
                bid = bid array(<price>, <whole lot volume>, <lot volume>)
                close = last trade closed array(<price>, <lot volume>)
                volume = volume array(<today>, <last 24 hours>)
                vwap = volume weighted average price array(<today>, <last 24 hours>)
                trades = number of trades array(<today>, <last 24 hours>)
                low = low array(<today>, <last 24 hours>)
                high = high array(<today>, <last 24 hours>)
                open = today's opening price
        """

        payload = {"pair": pair}
        response = await self.query_public(method="ticker", 
                                           data=payload,
                                           retries=retries
                                           )
        cols = {"a": "ask", 
               "b": "bid", 
               "c": "close",
               "v": "volume", 
               "p": "vwap", 
               "t": "trades", 
               "l": "low", 
               "h": "high", 
               "o": "open"}

        df = pd.DataFrame.from_dict(response, orient="index")
        df = df.rename(columns=cols)
        return df


    async def get_ohlc(self, pair: list, timeframe: int, since: int=None, retries=0) -> dict:
        """ Returns OHLC info

        Args:
            pair (list) : list containing single request pair 
            timeframe (int) : candle timeframe in minutes
                possible values : 1 (default), 5, 15, 30, 60, 240, 1440, 10080, 21600
            since : return committed OHLC data since given id (optional)
            retries (int): number of request retry attempts


        Returns:
            dict : {df, last}
                df : pandas.DataFrame 
                    index :  
                    columns :
                    time = unix timestamp
                    open 
                    high 
                    low
                    close
                    vwap
                    volume
                    count
                    last : unix timestamp 
                To be used as ``since`` when polling for new, committed OHLC Data
        """

        data = {"pair" : pair, "interval": timeframe, "since": since}
        response = await self.query_public(method="ohlc", 
                                           data=data,
                                           retries=retries
                                           )

        
        cols = ["time", "open", "high", "low", "close", "vwap", "volume", "count"]
        df = pd.DataFrame(response[pair[0].upper()], columns=cols) 
        last = int(response["last"])

        return {"df": df, "last": last}

    
    async def get_orderbook(self, pair: list, count: int=None, retries: int=0) -> dict:
        """
        Args:
            pair = asset pair to get market depth for
            count = maximum number of asks/bids (optional
        
        Returns:
            dict : {asks, bids}
                asks/bids = pandas.DataFrame
                columns : [price, volume, timestamp] 
        """

        data = {"pair": pair, "count": count}
        response = await self.query_public(method="orderbook",
                                          data=data,
                                          retries=retries
                                          )
        cols = ["price", "volume", "timestamp"]
        asks = pd.DataFrame(response[pair[0].upper()]["asks"], columns=cols)
        bids = pd.DataFrame(response[pair[0].upper()]["bids"], columns=cols)

        logging.warning(asks)

        return {"asks": asks, "bids": bids}


    async def get_trades(self, pair: list, since: int=None, retries: int=0) -> dict:
        """
        Args:
            pair (list): asset pair to get trade data for
            since (int): return trade data since given id (optional.  exclusive)

        Returns:
            pd.DataFrame
            index :
            columns : ["price", "volume", "time", "side", "type", "misc"]

        """

        data = {"pair": pair, "since": since}
        response = await self.query_public(method="trades",
                                           data=data,
                                           retries=retries
                                           ) 
        cols = ["price", "volume", "time", "side", "type", "misc"]
        df = pd.DataFrame(response[pair[0].upper()], columns=cols)
        #! all timestamps from response will need to be converted to int type
        return {"df": df, "last": int(response["last"])}       


    async def get_spread(self, pair: list, since: int=None, retries: int=0) -> dict:
        """
        Args:
            retries (int): 
            pair (list): asset pair to get spread data for
            since (int): return spread data since given id (optional.  inclusive)

        Returns:
            dict : {df, last}
                df : pandas.DataFrame
                index : 
                columns : [time, bid, ask] 
                last : id to be used as since when polling for new spread data
        """

        data = {"pair": pair, "since": since}
        response = await self.query_public(method="spread",
                                           data=data,
                                           retries=retries
                                           )

        cols = ["time", "bid", "ask"]
        df = pd.DataFrame(response[pair[0].upper()], columns=cols)
        return {"df": df, "last": int(response["last"])}




    # ====== Private Methods
    # ========================================


    async def get_account_balance(self, retries: int=0) -> dict:
        """Get account balance (holdings)

        Args:
            retries (int):

        Returns:
            dictionary
            {<asset name> : <balance amount>}
        """

        response = await self.query_private(method="account_balance", retries=retries)
        non_zero = balance_remove_zero_values(response)

        logging.warning(non_zero)
        return non_zero
        

    async def get_trade_balance(self, asset_class: str=None, asset: str=None, retries: int=0) -> pd.DataFrame:
        """Get trade balance (fiat equivalent)

        Args:
            asset_class (str): asset class (optional):
                currency (default)
            asset (str): base asset used to determine balance (default = ZUSD)

        Returns:
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
        return response


    async def get_open_orders(self, userref: int=None, trades: bool=True, retries: int=0) -> pd.DataFrame:
        """Get open orders

        Args:
            trades (bool): whether or not to include trades in output (optional.  default = false)
            userref (int): restrict results to given user reference id (optional)

        Returns:
            pandas.DataFrame
            index :
            columns : 
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
        
        df = pd.DataFrame.from_dict(response["open"], orient="index") # ==> better to orient along index
        return df


    async def get_closed_orders(self, offset: int=0, trades: bool=False, userref: int=None, start: int=None, end: int=None, closetime: str="both", retries: int=0) -> pd.DataFrame:
        """Get closed orders

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
            pandas.DataFrame
            index : 
            columns : 
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

        df = pd.DataFrame.from_dict(response["closed"], orient="index") # ==> better to orient along index 
        return df


    async def get_user_trades_history(self, trade_type: str="all", trades: bool=False, start: int=None, end: int=None, retries: int=0) -> pd.DataFrame:
        """Get the user's historical trades

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
        
        df = pd.DataFrame.from_dict(response["trades"], orient="index")
        return df       # we don't want to return "count" value as we can get it from df


    async def get_open_positions(self, txid: list=[], show_pnl=True, retries: int=0) -> pd.DataFrame:
        """Get info on open positions

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

        df = pd.DataFrame.from_dict(response, orient="index")
        return df




    # ==== Private User Trading
    # ========================================
    #! We should make sure to update cache and database every time we use these


    async def place_order(self, 
                          pair: list, 
                          side: str,
                          ordertype: str, 
                          volume: float,
                          price: float=None,
                          price2: float=None, 
                          leverage: int=None,
                          start_time: int=None,
                          expire_time: int=None,
                          userref: int=None,
                          validate: bool=False, 
                          oflags: list=[], 
                          retries: int=0
                          ):
        """ Place an order

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

    
    async def cancel_order(self, txid: str, retries: int=0):
        """Cancel an Open Order

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


    async def get_websocket_auth_token(self, validity: int=None, permissions: list=None, retries: int=0):
        """Get auth token to subscribe to private websocket feed

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