'''Define Base MetaClass for Exchange Rest APIs'''
from abc import ABC, abstractmethod
import time
import logging
import asyncio
from collections import deque
from typing import Optional
from typing_extensions import Literal

import ujson
import stackprinter
from pydantic import ValidationError
import pandas as pd

from noobit.server import settings
from noobit.logging.structlogger import get_logger
from noobit.models.data.receive.api import (Ticker, Ohlc, Orderbook, Trades, Spread,
                                            AccountBalance, TradeBalance, Order, OpenOrders,
                                            ClosedOrders, UserTrades, OpenPositions)
from noobit.models.data.response.order import OrdersList, OrdersByID


custom_logger = get_logger(__name__)

class APIBase():
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
            self.from_exchange_format = self._load_normalize_map()
            self.to_exchange_format = {v:k for k, v in self.normalize.items()}
            self.exchange_pair_specs = self._load_pair_specs_map()
    """

    env_keys_dq = deque()


    def __init__(self):

        self._load_all_env_keys()
        self.to_standard_format = self._load_normalize_map()
        self.to_exchange_format = {v:k for k, v in self.to_standard_format.items()}
        self.exchange_pair_specs = self._load_pair_specs_map()
        self.session = settings.SESSION
        self.response = None
        self._json_options = {}
        settings.SYMBOL_MAP_TO_EXCHANGE[self.exchange.upper()] = self.to_exchange_format
        settings.SYMBOL_MAP_TO_STANDARD[self.exchange.upper()] = self.to_standard_format


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
    # ==== AUTHENTICATION
    # ================================================================================


    # @abstractmethod
    # def _load_all_env_keys(self):
    #     '''Load all API keys from env file into a deque.

    #     Notes:
    #         In .env file, keys should contain :
    #             API Key : <exchange-name> & "key"
    #             API Secret : <exchange-name> & "secret"
    #     '''
    #     raise NotImplementedError


    # @abstractmethod
    # def _sign(self, data: dict, urlpath: str):
    #     raise NotImplementedError


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
        try:
            return self.env_keys_dq[0][0]
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

    def current_secret(self):
        """env secret we are currently using"""
        try:
            return self.env_keys_dq[0][1]
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))


    def _nonce(self):
        """Nonce counter.

        Returns:
            an always-increasing unsigned integer (up to 64 bits wide)
        """
        return int(1000*time.time())




    # ================================================================================
    # ==== UTILS
    # ================================================================================


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



    # @abstractmethod
    # def _load_normalize_map(self):
    #     '''Instantiate instance variable self.pair_map as dict.

    #     keys : exchange format
    #     value : standard format

    #     eg for kraken : {"XXBTZUSD": "XBT-USD", "ZUSD": "USD"}
    #     '''
    #     raise NotImplementedError



    # @abstractmethod
    # def _load_pair_specs_map(self):
    #     '''Instantiate instance variable self.pair_info as dict.

    #     keys : exchange format
    #     value : standard format

    #     eg for kraken : {"XBT-USD": {"price_decimals": 0.1, "volume_decimals": 0.1}}
    #     '''
    #     raise NotImplementedError



    # @abstractmethod
    # def _cleanup_input_data(self, data: dict):
    #     raise NotImplementedError



    # @abstractmethod
    # def _normalize_response(self, response: str):
    #     '''Input response has to be json string to make it easier to replace values.'''
    #     raise NotImplementedError



    # @abstractmethod
    # async def _handle_response_errors(self, response):
    #     '''Input response has to be json object.
    #     Needs to return none if there is an error and the data if there was no error.
    #     '''
    #     raise NotImplementedError




    # ================================================================================
    # ==== BASE QUERY METHODS
    # ================================================================================


    async def _query(self, endpoint, data: dict, private: bool, headers=None, timeout=None, retries=0):
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

        logging.debug(f"API Request URL: {self.response.url}")

        # return self.response.json(**self._json_options)

        resp_str = self.response.text
        # normalized_resp = self._normalize_response(resp_str)
        # normalized_resp = ujson.loads(normalized_resp)

        return ujson.loads(resp_str)




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

        # data = self._cleanup_input_data(data) ==> handled by request parser

        method_endpoint = self.public_methods[method]
        method_path = f"{self.public_endpoint}/{method_endpoint}"


        result = {"accept": False, "value": None}

        while not result["accept"]:

            resp = await self._query(endpoint=method_path,
                                     data=data,
                                     private=False,
                                     timeout=timeout,
                                     retries=retries
                                     )

            result = await self._handle_response_errors(response=resp)


        return result["value"]



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

        # data = self._cleanup_input_data(data) ==> this is handled by request parser
        data['nonce'] = self._nonce()

        method_endpoint = self.private_methods[method]
        method_path = f"{self.private_endpoint}/{method_endpoint}"


        headers = {
            'API-Key': self.current_key(),
            'API-Sign': self._sign(data, method_path)
        }

        result = {"accept": False, "value": None}

        while not result["accept"]:

            resp = await self._query(endpoint=method_path,
                                     data=data,
                                     headers=headers,
                                     private=True,
                                     timeout=timeout,
                                     retries=retries
                                     )

            self._rotate_api_keys()

            result = await self._handle_response_errors(response=resp)


        return result["value"]




    # ========================================
    # ================================================================================
    # ==== USER API QUERIES
    # ================================================================================
    # ========================================




    # ================================================================================
    # ====== PUBLIC REQUESTS
    # ================================================================================





    # ================================================================================
    # ====== PRIVATE REQUESTS
    # ================================================================================


    # @abstractmethod
    # async def get_open_orders(self,
    #                           mode: Literal["to_list", "by_id"],
    #                           symbol: str,
    #                           clOrdID: str,
    #                           retries: int
    #                           ):
    #     """Get open orders

    #     Args:
    #         symbol (str): Instrument symbol
    #         clOrdID (str): Restrict results to given ID
    #         mode (str): Parse response to list or index by order id

    #     Returns:
    #         parsed response
    #     """
    #     raise NotImplementedError


    # @abstractmethod
    # async def get_closed_orders(self,
    #                             mode: Literal["to_list", "by_id"],
    #                             symbol: str,
    #                             clOrdID: str,
    #                             retries: int
    #                             ):

    #     raise NotImplementedError



    async def get_order(self,
                        mode: Literal["to_list", "by_id"],
                        orderID: str,
                        clOrdID: Optional[int] = None,
                        retries: int = 1
                        ):
        """Get a single order
            mode (str): Parse response to list or index by order id
            orderID: ID of the order to query (ID as assigned by broker)
            clOrdID (str): Restrict results to given ID
        """
        data = self.request_parser.order("closed", orderID, clOrdID)

        response = await self.query_private(method="order_info", data=data, retries=retries)
        # parse to order response model and validate
        parsed_response = self.response_parser.order_response(response=response, mode=mode)

        return parsed_response




    async def get_open_orders(self,
                              mode: Literal["to_list", "by_id"],
                              symbol: Optional[str] = None,
                              clOrdID: Optional[int] = None,
                              retries: int = 1
                              ):
        """Get open orders.

        Args:
            mode (str): Parse response to list or index by order id
            symbol (str): Instrument symbol
            clOrdID (str): Restrict results to given ID

        Returns:
            open orders
        """

        data = self.request_parser.order("open", symbol=symbol, clOrdID=clOrdID)

        response = await self.query_private(method="open_orders", data=data, retries=retries)
        # parse to order response model
        parsed_response = self.response_parser.order(response=response, symbol=symbol, mode=mode)

        # don't let responsability of validation to user ==> force it here instead
        if mode == "to_list":
            try:
                validated_data = OrdersList(data=parsed_response)
            except ValidationError as e:
                raise e

        if mode == "by_id":
            try:
                validated_data = OrdersByID(data=parsed_response)
            except ValidationError as e:
                raise e

        try:
            return validated_data.data
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))



    async def get_closed_orders(self,
                                mode: Literal["to_list", "by_id"],
                                symbol: Optional[str] = None,
                                clOrdID: Optional[int] = None,
                                retries: int = 1
                                ):
        """Get closed orders.

        Args:
            symbol (str): Instrument symbol
            clOrdID (str): Restrict results to given ID
            mode (str): Parse response to list or index by order id

        Returns:
            closed orders
        """

        data = self.request_parser.order("closed", symbol=symbol, clOrdID=clOrdID)

        response = await self.query_private(method="closed_orders", data=data, retries=retries)
        # parse to order response model and validate
        parsed_response = self.response_parser.order(response=response, symbol=symbol, mode=mode)

        # don't let responsability of validation to user ==> force it here instead
        if mode == "to_list":
            try:
                validated_data = OrdersList(data=parsed_response)
            except ValidationError as e:
                raise e

        if mode == "by_id":
            try:
                validated_data = OrdersByID(data=parsed_response)
            except ValidationError as e:
                raise e

        try:
            return validated_data.data
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))





    # ================================================================================
    # ====== TRADING REQUESTS
    # ================================================================================


    async def place_order(self,
                              symbol,
                              side,
                              ordType,
                              execInst,
                              clOrdID,
                              timeInForce,
                              effectiveTime,
                              expireTime,
                              orderQty,
                              orderPercent,
                              price,
                              stopPx,
                              targetStrategy,
                              targetStrategyParameters
                              ):
        pass

    # @abstractmethod
    # async def place_order(self, *args, **kwargs):
    #     raise NotImplementedError



    # @abstractmethod
    # async def cancel_order(self, *args, **kwargs):
    #     raise NotImplementedError



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




    # ================================================================================
    # ==== WRITE ALL HISTORICAL OHLC TO CSV
    # ================================================================================


    async def write_historical_trades_to_csv(self, pair: list):
        """
        kraken does not provide historical ohlc data
        ==> aggregate all historical trades into ohlc
        """

        file_path = f"data/{self.exchange.lower()}_{pair[0]}_historical_trade_data.csv"

        # init
        since = 0
        count = 0

        # verify data validity
        try:
            df = pd.read_csv(file_path,
                             names=["price", "volume", "time", "side", "type", "misc"],
                            #  header=None,
                            #  skiprows=1
                             )
            # logging.info(df.head(10))
            logging.info(df.tail(10))
            # logging.info(df.dtypes)

            # get index for row with highest timestamp
            max_ts = df["time"].max()
            [max_ts_index] = df.index[df["time"] == max_ts].tolist()

            # drop row where index > max_ts_index
            # (means they were wrongly appended to file)
            df = df[(df["time"] < max_ts) & (df.index < max_ts_index)]

            # overwrite
            df.to_csv(path_or_buf=file_path,
                      mode="w",
                      header=False,
                      index=False
                      )

            since = int(df["time"].iloc[-1] * 10**9)
            # logging.info(df.head(10))
            logging.info(df.tail(10))
            logging.info(f"Last trade entry written to csv for date : {pd.to_datetime(since)}")
        except FileNotFoundError as e:
            logging.warning("CSV file does not exist")
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))


        logging.info(f"since: {since} --- type: {type(since)}")

        most_recent_trades = await self.get_trades(pair=pair)
        most_recent_last = most_recent_trades["last"]

        try:
            while since < most_recent_last:
                trades = await self.get_trades(pair=pair, since=since)
                trades_df = pd.DataFrame(trades["data"])
                trades_df.to_csv(path_or_buf=file_path,
                                 mode="a",
                                 header=False,
                                 index=False
                                 )
                count += len(trades["data"])
                since = trades["last"]
                # otherwise we will get rate limited
                await asyncio.sleep(2)
                custom_logger.info(f"count : {count}")
                custom_logger.info(pd.to_datetime(int(since)))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

        return {"count": count}
