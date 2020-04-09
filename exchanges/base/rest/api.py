'''Define Base MetaClass for Exchange Rest APIs'''
from abc import ABC, abstractmethod
import time
import logging

import ujson
import stackprinter
from pydantic import ValidationError
import pandas as pd

from models.data.receive.api import (Ticker, Ohlc, Orderbook, Trades, Spread, AccountBalance,
                                     TradeBalance, OpenOrders, ClosedOrders, UserTrades, OpenPositions)


class BaseRestAPI(ABC):
    """Abstract Baseclass for Rest APIs.

    Notes:
        Example Init for Kraken:
            self.exchange = "Kraken"
            self.base_url = mapping[self.exchange]["base_url"]
            self.public_endpoint = mapping[self.exchange]["public_endpoint"]
            self.private_endpoint = mapping[self.exchange]["private_endpoint"]
            self.public_methods = mapping[self.exchange]["public_methods"]
            self.private_methods = mapping[self.exchange]["private_methods"]
            self.session = settings.SESSION
            self.response = None
            self._json_options = {}
            self._load_all_env_keys()
            self.normalize = self._load_normalize_map()
    """


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


    @abstractmethod
    def _load_all_env_keys(self):
        '''Load all API keys from env file into a deque.

        Notes:
            In .env file, keys should contain :
                API Key : <exchange-name> & "key"
                API Secret : <exchange-name> & "secret"
        '''
        raise NotImplementedError


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
        """env key we are currently using"""
        return self.env_keys_dq[0][0]


    def current_secret(self):
        """env secret we are currently using"""
        return self.env_keys_dq[0][1]


    def _nonce(self):
        """Nonce counter.

        Returns:
            an always-increasing unsigned integer (up to 64 bits wide)
        """
        return int(1000*time.time())


    def _sign(self, data: dict, urlpath: str):
        raise NotImplementedError




    # ================================================================================
    # ================================================================================
    # ==== UTILS


    async def retry(self, *, func: object, retry_attempts: int = 0, **kwargs):
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

    @abstractmethod
    def _load_normalize_map(self):
        '''Instantiate instance variable self.pair_map as dict.

        keys : exchange format
        value : standard format

        eg for kraken : {"xxbtzusd": "btc/usd", "zusd": "usd}
        '''
        raise NotImplementedError




    @abstractmethod
    def _cleanup_input_data(self, data: dict):
        raise NotImplementedError


    @abstractmethod
    def _normalize_response(self, response: str):
        '''Input response has to be json string to make it easier to replace values.'''
        raise NotImplementedError


    @abstractmethod
    def _handle_response_errors(self, response):
        '''Input response has to be json object.
        Needs to return none if there is an error and the data if there was no error.
        '''
        raise NotImplementedError




    # ================================================================================
    # ================================================================================
    # ==== BASE QUERY METHODS


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

        #   KRAKEN Docs :
        #   Public methods can use either GET or POST.
        #   Private methods must use POST and be set up as follows [...]
        #   This should also work for other exchanges

        if private:
            self.response = await self.retry(func=self.session.post,
                                             url=full_path,
                                             data=data,
                                             json=json,
                                             headers=headers,
                                             timeout=timeout,
                                             retry_attempts=retries
                                             )

        else:
            self.response = await self.retry(func=self.session.get,
                                             url=full_path,
                                             params=data,
                                             timeout=timeout,
                                             retry_attempts=retries
                                             )

        if self.response.status_code not in (200, 201, 202):
            self.response.raise_for_status()

        logging.debug(f"API Request for url : {self.response.url}")

        # return self.response.json(**self._json_options)

        # we return text so it is easier to replace pairs and currencies to standard format
        resp_str = self.response.text
        normalized_resp = self._normalize_response(resp_str)
        normalized_resp = ujson.loads(normalized_resp)

        return normalized_resp




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

        data = self._cleanup_input_data(data)

        method_endpoint = self.public_methods[method]
        method_path = f"{self.public_endpoint}/{method_endpoint}"

        resp = await self._query(endpoint=method_path,
                                 data=data,
                                 private=False,
                                 timeout=timeout,
                                 retries=retries
                                 )

        result = self._handle_response_errors(resp)
        if result is not None:
            return result



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

        data = self._cleanup_input_data(data)
        data['nonce'] = self._nonce()

        method_endpoint = self.private_methods[method]
        method_path = f"{self.private_endpoint}/{method_endpoint}"


        headers = {
            'API-Key': self.current_key(),
            'API-Sign': self._sign(data, method_path)
        }

        resp = await self._query(endpoint=method_path,
                                 data=data,
                                 headers=headers,
                                 private=True,
                                 timeout=timeout,
                                 retries=retries
                                 )

        self._rotate_api_keys()

        result = self._handle_response_errors(resp)
        if result is not None:
            return result




    # ========================================
    # ================================================================================
    # ==== USER API QUERIES
    # ================================================================================
    # ========================================




    # ================================================================================
    # ====== Public Methods
    # ================================================================================


    @abstractmethod
    async def get_raw_ticker(self, *args, **kwargs) -> dict:
        """Raw (not checked against our models) ticker data for given pairs.

        Args:
            pair (list) : list of requested pairs
                input format : ["XBT-USD", "ETH-USD"]
                must be passed as list even if single pair
            retries (int): number of request retry attempts

        Returns:
            dict that must follow models.orm.Ticker data model
        """
        raise NotImplementedError



    async def get_ticker(self, pair: list, retries: int = 0) -> dict:
        """Validated Ticker data (checked against data model).

        Args:
            pair (list) : list of requested pairs
                input format : ["XBT-USD", "ETH-USD"]
                must be passed as list even if single pair
            retries (int): number of request retry attempts

        Returns:
            dict with single key:
                data (dict):
                    key (str) : pair
                    value (list) : array of ask, bid, open, high, low, close, volume, vwap, trades
        """

        data = await self.get_raw_ticker(pair, retries)
        try:
            ticker = Ticker(data=data)
            return ticker.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_ticker method returns the correct type")
            logging.error(e)



    async def get_ticker_as_pandas(self, pair: list, retries: int = 0):
        """Checked ticker data for given pairs as pandas df.
        """
        validated_response = await self.get_ticker(pair, retries)

        df = pd.DataFrame.from_dict(validated_response["data"], orient="index") # ==> better to orient along index
        return df



    @abstractmethod
    async def get_raw_ohlc(self, *args, **kwargs) -> dict:
        """Raw Ohlc data (not yet validated against data model).

        Args:
            pair (list) : list containing single request pair
            timeframe (int) : candle timeframe in minutes
                possible values : 1 (default), 5, 15, 30, 60, 240, 1440, 10080, 21600
            since : return committed OHLC data since given id (optional)
            retries (int): number of request retry attempts


        Returns:
            dict (must conform with models.data_models.Ohlc):
                data (list) : array of <time>, <open>, <high>, <low>, <close>, <vwap>, <volume>, <count>
                    vwap and count are optional, can be none
                last (Decimal) : id to be used as since when polling for new, committed OHLC data
        """
        raise NotImplementedError



    async def get_ohlc(self, pair: list, timeframe: int, since: int = None, retries: int = 0):
        """Validated Ohlc data (checked against data model).

        Args:
            pair (list) : asset pair to get market depth for
            timeframe (int) : candle timeframe in minutes
                possible values : 1 (default), 5, 15, 30, 60, 240, 1440, 10080, 21600
            since : return committed OHLC data since given id (optional)
            retries (int): number of request retry attempts

        Returns:
            dict with only two keys:
                data (list) : array of <time>, <open>, <high>, <low>, <close>, <vwap>, <volume>, <count>
                    vwap and count are optional, can be none
                last (Decimal) : id to be used as since when polling for new, committed OHLC data
        """
        response = await self.get_raw_ohlc(pair, timeframe, since, retries)
        try:
            ohlc = Ohlc(data=response["data"], last=response["last"])
            return ohlc.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_ohlc method returns the correct type")
            logging.error(e)



    async def get_ohlc_as_pandas(self, pair: list, timeframe: int, since: int = None, retries: int = 0):
        """Validated Ohlc data as pandas dataframe.

        Returns:
            dict: two keys
                data (pd.DataFrame)
                last (int)

        """
        validated_response = await self.get_ohlc(pair, timeframe, since, retries)

        cols = ["time", "open", "high", "low", "close", "vwap", "volume", "count"]
        df = pd.DataFrame(data=validated_response["data"], columns=cols)
        return {"data": df, "last": validated_response["last"]}



    @abstractmethod
    async def get_raw_orderbook(self, *args, **kwargs) -> dict:
        raise NotImplementedError



    async def get_orderbook(self, pair: list, count: int = None, retries: int = 0):
        """Validated orderbook data (checked against data model).

        Args:
            pair (list) : asset pair to get market depth for
            count (int) : maximum number of asks/bids (optional)
            retries (int): number of request retry attempts

        Returns:
            dict with only two keys:
                asks (list) : array of <price>, <volume>, <timestamp>
                bids (list) : array of <price>, <volume>, <timestamp>
        """
        response = await self.get_raw_orderbook(pair, count, retries)
        try:
            ob = Orderbook(asks=response["asks"], bids=response["bids"])
            return ob.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_orderbook method returns the correct type")
            logging.error(e)



    async def get_orderbook_as_pandas(self, pair: list, count: int = None, retries: int = 0):
        """Validated orderbook data as pandas dataframe.

        Returns:
            dict: 2 keys
                asks (pd.DataFrame)
                bids (pd.DataFrame)
        """
        #   TODO : merge the two dataframes and return
        validated_response = await self.get_orderbook(pair, count, retries)

        cols = ["price", "volume", "timestamp"]
        asks_df = pd.DataFrame(data=validated_response["asks"], columns=cols)
        bids_df = pd.DataFrame(data=validated_response["bids"], columns=cols)
        return {"asks": asks_df, "bids": bids_df}



    @abstractmethod
    async def get_raw_trades(self, *arg, **kwargs) -> dict:
        """Raw Trades data (not yet validated against data model).

        Args:
            pair (list): asset pair to get trade data for
            since (int): return trade data since given id (optional.  exclusive)

        Returns:
            dict : two keys
                data (list) : array of <price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>
                last (int) : id to be used as since when polling for new data
        """
        raise NotImplementedError



    async def get_trades(self, pair: list, since: int = None, retries: int = 0):
        """Validated Trades data (checked against data model).

        Args:
            pair (list): asset pair to get trade data for
            since (int): return trade data since given id (optional.  exclusive)

        Returns:
            dict : two keys
                data (list) : array of <price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>
                last (Decimal) : id to be used as since when polling for new data
        """
        response = await self.get_raw_trades(pair, since, retries)
        try:
            trades = Trades(data=response["data"], last=response["last"])
            return trades.dict()
        except ValidationError as e:
            logging.warning("Please check that get_raw_trades method returns the correct type")
            logging.error(stackprinter.format(e, style="darkbg2"))



    async def get_trades_as_pandas(self, pair: list, since: int = None, retries: int = 0):
        """Validated Trades data (checked against data model).

        Args:
            pair (list): asset pair to get trade data for
            since (int): return trade data since given id (optional.  exclusive)

        Returns:
            dict : two keys
                data (pd.DataFrame) : columns <price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>
                last (Decimal) : id to be used as since when polling for new data
        """
        validated_response = await self.get_trades(pair, since, retries)

        cols = ["price", "volume", "time", "side", "type", "misc"]
        df = pd.DataFrame(data=validated_response["data"], columns=cols)
        return {"data": df, "last": validated_response["last"]}



    @abstractmethod
    async def get_raw_spread(self, *args, **kwargs) -> dict:
        """Raw Spread data (not yet validated against data model).

        Args:
            pair (list): asset pair to get trade data for
            since (int): return data since given id (optional.  exclusive)
            retries(int)

        Returns:
            dict : two keys
                data (list) : array of entries <time>, <bid>, <ask>
                last (Decimal) : id to be used as since when polling for new data
        """
        raise NotImplementedError


    async def get_spread(self, pair: list, since: int = None, retries: int = 0):
        """Validated Spread data (checked against data model).

        Args:
            pair (list): asset pair to get trade data for
            since (int): return trade data since given id (optional.  exclusive)
            retries(int)

        Returns:
            dict : two keys
                data (list) : array of <time>, <bid>, <ask>
                last (Decimal) : id to be used as since when polling for new data
        """
        response = await self.get_raw_spread(pair, since, retries)
        try:
            trades = Spread(data=response["data"], last=response["last"])
            return trades.dict()
        except ValidationError as e:
            logging.warning("Please check that get_raw_spread method returns the correct type")
            logging.error(e)


    async def get_spread_as_pandas(self, pair: list, since: int = None, retries: int = 0) -> pd.DataFrame:
        """Validated Spread data as pandas dataframe.

        Args:
            pair (list): asset pair to get trade data for
            since (int): return trade data since given id (optional.  exclusive)
            retries(int)

        Returns:
            dict : two keys
                data (pd.DataFrame) : columns of <time>, <bid>, <ask>
                last (Decimal) : id to be used as since when polling for new data
        """

        validated_response = await self.get_spread(pair, since, retries)

        cols = ["time", "bid", "ask"]
        df = pd.DataFrame(data=validated_response["data"], columns=cols)
        return {"data": df, "last": validated_response["last"]}





    # ================================================================================
    # ====== PRIVATE REQUESTS
    # ================================================================================


    @abstractmethod
    async def get_raw_account_balance(self, *args, **kwargs) -> dict:
        raise NotImplementedError


    async def get_account_balance(self, retries: int = 0) -> dict:
        """Validated account balance data (checked against data model).

        Args:
            retries (int)

        Returns:
            dictionary : one key
                data (dict) : dict of <asset name> : <balance amount>
        """
        response = await self.get_raw_account_balance(retries)
        try:
            account_balance = AccountBalance(data=response)
            return account_balance.dict()
        except ValidationError as e:
            logging.warning("Please check that get_raw_account_balance method returns the correct type")
            logging.error(e)


    async def get_account_balance_as_pandas(self, retries: int = 0) -> pd.DataFrame:
        """Probably useless.
        """
        validated_response = await self.get_account_balance(retries)
        df = pd.DataFrame.from_dict(validated_response["data"], orient="index") # ==> better to orient along index
        return df



    @abstractmethod
    async def get_raw_trade_balance(self, *args, **kwargs) -> dict:
        """Trade balance data (not validated against data model).

        Args:
            asset_class (str): asset class (optional):
                currency (default)
            asset (str): base asset used to determine balance (default = ZUSD)

        Returns:
            dict with following keys

                - equivalent_balance (combined balance of all currencies)
                - trade_balance (combined balance of all equity currencies)
                - positions_margin
                - positions_unrealized (net profit/loss of open positions)
                - positions_cost basis
                - positions_valuation
                - equity (trade balance + unrealized net profit/loss)
                - free_margin (equity - initial margin)
                    (maximum margin available to open new positions)
                - margin_level ( equity*100 / initial margin )

        Note:
            I dont't really understand what is meant by asset_class input in the API Docs
        """
        raise NotImplementedError



    async def get_trade_balance(self, asset_class: str = None, asset: str = None, retries: int = 0) -> dict:
        """Trade balance data (not validated against data model).

        Args:
            asset_class (str): asset class (optional):
                currency (default)
            asset (str): base asset used to determine balance (default = ZUSD)

        Returns:
            dict : one key

                data (dict) : with following keys:

                - equivalent_balance (combined balance of all currencies)
                - trade_balance (combined balance of all equity currencies)
                - positions_margin
                - positions_unrealized (net profit/loss of open positions)
                - positions_cost basis
                - positions_valuation
                - equity (trade balance + unrealized net profit/loss)
                - free_margin (equity - initial margin)
                    (maximum margin available to open new positions)
                - margin_level ( equity*100 / initial margin )

        Note:
            I dont't really understand what is meant by asset_class input in the API Docs
        """
        response = await self.get_raw_trade_balance(asset_class, asset, retries)
        try:
            trade_balance = TradeBalance(data=response)
            return trade_balance.dict()
        except ValidationError as e:
            logging.warning("Please check that get_raw_trade_balance method returns the correct type")
            logging.error(e)


    async def get_trade_balance_as_pandas(self, asset_class: str = None,
                                          asset: str = None,
                                          retries: int = 0
                                          ) -> pd.DataFrame:
        """Get validated Trade Balance data as pandas df
        """
        validated_response = await self.get_trade_balance(asset_class, asset, retries)
        df = pd.DataFrame.from_dict(validated_response["data"], orient="index") # ==> better to orient along index
        return df



    @abstractmethod
    async def get_raw_open_orders(self, *args, **kwargs) -> dict:
        """Raw open orders data (not validated against data model).

        Args:
            trades = whether or not to include trades in output
                (optional.  default = false)
            userref = restrict results to given user reference id
                (optional)

        Returns:
            dict with ordertxid as key and orderinfo as value:
                orderinfo :
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
        """
        raise NotImplementedError


    async def get_open_orders(self, userref: int = None, trades: bool = True, retries: int = 0) -> dict:
        """Open orders data (checked against data model).
        Args:
            trades = whether or not to include trades in output
                (optional.  default = false)
            userref = restrict results to given user reference id
                (optional)

        Returns:
            dict with ordertxid as key and orderinfo as value:
                orderinfo :
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
        """
        response = await self.get_raw_open_orders(userref, trades, retries)
        try:
            open_orders = OpenOrders(data=response)
            return open_orders.dict()
        except ValidationError as e:
            logging.warning("Please check that get_raw_open_orders method returns the correct type")
            logging.error(e)


    async def get_open_orders_as_pandas(self, userref: int = None, trades: bool = True, retries: int = 0):
        """Get Open Order data as pandas df
        """
        validated_response = await self.get_open_orders(userref, trades, retries)
        df = pd.DataFrame.from_dict(validated_response["data"], orient="index") # ==> better to orient along index
        return df


    @abstractmethod
    async def get_raw_closed_orders(self, *args, **kwargs) -> dict:
        raise NotImplementedError


    async def get_closed_orders(self, offset: int = 0,
                                trades: bool = False,
                                userref: int = None,
                                start: int = None,
                                end: int = None,
                                closetime: str = "both",
                                retries: int = 0
                                ) -> dict:
        """Validated closed orders data (checked against data model).
        """

        response = await self.get_raw_closed_orders(offset, trades, userref, start, end, closetime, retries)
        try:
            closed_orders = ClosedOrders(data=response)
            return closed_orders.dict()
        except ValidationError as e:
            logging.warning("Please check that get_raw_closed_orders method returns the correct type")
            logging.error(e)


    async def get_closed_orders_as_pandas(self, offset: int = 0,
                                          trades: bool = False,
                                          userref: int = None,
                                          start: int = None,
                                          end: int = None,
                                          closetime: str = "both",
                                          retries: int = 0
                                          ) -> pd.DataFrame:

        validated_response = await self.get_closed_orders(offset, trades, userref, start, end, closetime, retries)
        df = pd.DataFrame.from_dict(validated_response["data"], orient="index")
        return df



    @abstractmethod
    async def get_raw_user_trades(self, *args, **kwargs) -> pd.DataFrame:
        raise NotImplementedError


    async def get_user_trades(self, trade_type: str = "all",
                              trades: bool = False,
                              start: int = None,
                              end: int = None,
                              retries: int = 0
                              ) -> dict:
        """Validated user trades data (checked against data model).
        """
        response = await self.get_raw_user_trades(trade_type, trades, start, end, retries)
        try:
            user_trades = UserTrades(data=response)
            return user_trades.dict()
        except ValidationError as e:
            logging.warning("Please check that your raw method returns the correct type")
            logging.error(e)


    async def get_user_trades_as_pandas(self, trade_type: str = "all",
                                        trades: bool = False,
                                        start: int = None,
                                        end: int = None,
                                        retries: int = 0
                                        ) -> pd.DataFrame:
        """Get validated user trades data as pandas df
        """
        validated_response = await self.get_user_trades(trade_type, trades, start, end, retries)
        df = pd.DataFrame.from_dict(validated_response["data"], orient="index")
        return df



    @abstractmethod
    async def get_raw_open_positions(self, *args, **kwargs) -> dict:
        raise NotImplementedError


    async def get_open_positions(self, txid: list = None, show_pnl=True, retries: int = 0) -> dict:
        """Validated open positions data (checked against data model).

        Args:
            txid (str) : transaction ids to restrict output to
            show_pnl (bool): whether or not to include profit/loss calculations
            retries (int)

        Returns:
            dict : single key <data>
                data (dict) : position_txid as key and pos_info dict as value
                    pos_info:
                    ordertxid = order responsible for execution of trade
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
        response = await self.get_raw_open_positions(txid, show_pnl, retries)
        try:
            open_positions = OpenPositions(data=response)
            return open_positions.dict()
        except ValidationError as e:
            logging.warning("Please check that your raw method returns the correct type")
            logging.error(e)


    async def get_open_positions_as_pandas(self, txid: list = None, show_pnl=True, retries: int = 0) -> pd.DataFrame:
        """Get validated open positions data as pandas df
        """
        validated_response = await self.get_open_positions(txid, show_pnl, retries)
        df = pd.DataFrame.from_dict(validated_response["data"], orient="index")
        return df



    # ================================================================================
    # ====== TRADING REQUESTS
    # ================================================================================


    @abstractmethod
    async def place_order(self, *args, **kwargs):
        raise NotImplementedError


    @abstractmethod
    async def cancel_order(self, *args, **kwargs):
        raise NotImplementedError


    async def cancel_all_orders(self, retries: int = 0):
        """Cancel all orders and return count of how many we canceled"""
        count = 0
        id_list = []
        response = await self.get_open_orders(retries=retries)
        open_orders = response["data"]
        for order_id, _ in open_orders.items():
            await self.cancel_order(order_id, retries=retries)
            count += 1
            id_list.append(order_id)
        return {"canceled": id_list, "count": count}


    async def close_all_positions(self, retries: int = 0):
        """Close all positions and return count of how many we closed"""
        count = 0
        id_list = []
        response = await self.get_open_positions(retries=retries)
        open_positions = response["data"]
        for pos_id, pos_info in open_positions.items():
            # how to we close a position ?
            # we need to place an order, maybe using the "settle-position" arg
            # not well documented
            # should we write a close_position(pos_id) method ?
            pass
