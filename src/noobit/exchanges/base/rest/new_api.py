'''Define Base MetaClass for Exchange Rest APIs'''
from abc import ABC, abstractmethod
import time
import logging
import asyncio
from collections import deque
from typing import Optional, Union, Any, Dict
from typing_extensions import Literal

import ujson
import stackprinter
from pydantic import BaseModel, ValidationError
import pandas as pd
from starlette import status

from noobit.server import settings
from noobit.logging.structlogger import get_logger
from noobit.models.data.receive.api import (Ticker, Orderbook, Trades, Spread,
                                            AccountBalance, TradeBalance, Order, OpenOrders,
                                            ClosedOrders, UserTrades, OpenPositions)
from noobit.models.data.response.order import OrdersList, OrdersByID
from noobit.models.data.response.trade import TradesList, TradesByID
from noobit.models.data.response.ohlc import Ohlc
from noobit.models.data.base.errors import ErrorHandlerResult, BaseError, OKResult, ErrorResult
from noobit.models.data.base.types import PAIR, TIMEFRAME
from noobit.models.data.base.response import NoobitResponse, OKResponse, ErrorResponse
from noobit.models.data.request.parse.base import BaseRequestParser
from noobit.models.data.response.parse.base import BaseResponseParser


custom_logger = get_logger(__name__)

class APIBase():
    """Baseclass for Rest APIs.
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

        # must be defined by user
        # self.request_parser = BaseRequestParser
        # self.response_parser = BaseResponseParser


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



    async def _handle_response_errors(self, response, endpoint, data) -> ErrorHandlerResult:

        try:
            result = self.response_parser.handle_errors(response, endpoint, data)
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

        #! how can we type check this ? do we need to ?
        #! raw response should not be type checked because we have no way of knowing types
        #! exception should be type checked ?
        #! ==> we basically want to make sure that user will return a dict of format {"accept": bool, "value": Any}
        #! ==> should he return a dict or encapsulate the data in a object that will force type ??
        # try:
        #     logging.warning(result)
        #     # validated_result = ErrorHandlerResult(**result)
        #     validated_result = OKResult(result.dict())
        # except ValidationError as e:
        #     logging.error(e)
        #     return ErrorResult(accept=True, value=str(e))
        if not isinstance(result, ErrorHandlerResult):
            error_msg = "Invalid Type: Result needs to be ErrorResult or OKResult"
            logging.error(error_msg)
            return ErrorResult(accept=True, value=error_msg)


        # if isinstance(validated_result.value, BaseError):
        if not result.is_ok:
            # result["value"] returns one of our custom error classes here
            # exception = result.value
            logging.error(result.value)

            #! We now return ErrorResult() and simply pass the string representation of our error to value
            #! (instead of passing a dict and type checking here)
            #! So we can not call attributes anymore ...
            #! How do we solve this mess
            if result.sleep:
                await asyncio.sleep(result.sleep)
            return result

        else:
            return result



    # ================================================================================
    # ==== BASE QUERY METHODS
    # ================================================================================


    async def _query(self, endpoint, data: dict, private: bool, headers: dict = None, timeout: Union[float, int] = None, retries: int = 0):
        """ Low-level query handling.

        Args:
            endpoint (str): API URL path sans host
            data (dict): API request parameters
            headers (dict): HTTPS headers (optional)
            timeout (float): if not None, exception will be thrown after timeout seconds if a response has not been received

        Returns:
            requests.Response.json: deserialized python object

        Raises:
            requests.HTTPError: if response status not successful

        Note:
           Use :py:meth:`query_private` or :py:meth:`query_public`
           unless you have a good reason not to.
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




    async def query_public(self, method: str, data: dict = None, timeout: Union[float, int] = None, retries: int = 0):
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



        # retry while we have not accepted what the response returns
        # handle_response_errors should return a dict of format {"accept": True, "value": response}
        #! this is actually stupid as it may loop forever with no max retry number
        result = ErrorResult(accept=False, value="")

        while not result.accept:

            resp = await self._query(endpoint=method_path,
                                     data=data,
                                     private=False,
                                     timeout=timeout,
                                     retries=retries
                                     )

            # returns an ErrorHandlerResult object
            result = await self._handle_response_errors(response=resp, endpoint=method_path, data=data)


        return result




    async def query_private(self, method: str, data: dict = None, timeout: Union[float, int] = None, retries: int = 0) -> Union[ErrorResult, OKResult]:
        """ Performs an API query that requires a valid key/secret pair.

        Args:
            method (str): API method name
            data (dict): (optional) API request parameters
            timeout (float) : (optional)
                if not ``None``, throw Error after ``timeout`` seconds if no response

        Returns:
            noobit.ErrorHandlerResult
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

        result = ErrorResult(accept=False, value="")

        while not result.accept:

            resp = await self._query(endpoint=method_path,
                                     data=data,
                                     headers=headers,
                                     private=True,
                                     timeout=timeout,
                                     retries=retries
                                     )

            self._rotate_api_keys()

            # returns an ErrorHandlerResult object
            result = await self._handle_response_errors(response=resp, endpoint=method_path, data=data)


        return result




    # ========================================
    # ================================================================================
    # ==== USER API QUERIES
    # ================================================================================
    # ========================================


    def validate_model_from_mode(self,
                                 parsed_response: Union[dict, list, str],
                                 mode: Optional[str],
                                 mode_to_model: Dict[str, BaseModel]
                                 ) -> Union[OKResponse, ErrorResponse]:
        """Handle validation for all possible modes present in mode_to_model dict

        Args:
            parsed_response: object to validate
            mode: mode of request
            mode_to_model: dict mapping mode to pydantic model to validate against

        Returns:
            Union[OKResponse, ErrorResponse]: according to success/error
        """

        pydantic_model = mode_to_model[mode]

        try:
            validated = pydantic_model(data=parsed_response)
            return OKResponse(status_code=status.HTTP_200_OK,
                              # we need to call dict method because validated.data would return Dict[str, Order]
                              # which is not json serializable
                              #! python datetime is not serializable so will json output will be unix ts
                              value=validated.dict()["data"]
                              # value=validated.data
                              )

        except ValidationError as e:
            logging.error(e)
            return ErrorResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                  value=str(e)
                                  )



    # ================================================================================
    # ====== PUBLIC REQUESTS
    # ================================================================================

    def ohlc_validate_and_serialize(self, parsed_response):

        mode_to_model = {
            "ohlc": Ohlc
        }

        return self.validate_model_from_mode(parsed_response, mode="ohlc", mode_to_model=mode_to_model)



    async def get_ohlc(self,
                       symbol: PAIR,
                       timeframe: TIMEFRAME,
                       retries: int = 1
                       ) -> NoobitResponse:
        """
        """
        data = {"pair": symbol, "interval": timeframe}
        # data = self.request_parser.ohlc(symbol=symbol, timeframe=timeframe)

        result = await self.query_public(method="ohlc", data=data, retries=retries)
        # parse to order response model and validate
        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.ohlc(response=result.value)
            return self.ohlc_validate_and_serialize(parsed_response)


    # ================================================================================


    def public_trade_validate_and_serialize(self, parsed_response):

        mode_to_model = {
            "public_trade": TradesList
        }

        return self.validate_model_from_mode(parsed_response, mode="public_trade", mode_to_model=mode_to_model)


    async def get_public_trades(self,
                                symbol: PAIR,
                                retries: int = 1
                                ) -> NoobitResponse:
        """
        """
        data = {"pair": symbol}
        # data = self.request_parser.ohlc(symbol=symbol, timeframe=timeframe)

        result = await self.query_public(method="trades", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.trades(response=result.value)
            return self.public_trade_validate_and_serialize(parsed_response)




    # ================================================================================
    # ====== PRIVATE REQUESTS
    # ================================================================================


    def balance_validate_and_serialize(self, mode, parsed_response):
        pass



    async def get_balance(self):
        pass


    # ================================================================================




    #! this should probably return some custom response class
    def order_validate_and_serialize(self,
                                     mode: Literal["to_list", "by_id"],
                                     parsed_response: Union[dict, list, str],
                                     ) -> NoobitResponse:

        # don't let responsability of validation/serialization to user ==> force it here instead
        mode_to_model = {
            "by_id": OrdersByID,
            "to_list": OrdersList
        }

        return self.validate_model_from_mode(parsed_response, mode, mode_to_model)



    async def get_order(self,
                        mode: Literal["to_list", "by_id"],
                        orderID: str,
                        clOrdID: Optional[int] = None,
                        retries: int = 1
                        ) -> Union[list, dict, str]:
        """Get a single order
            mode (str): Parse response to list, or index by order id
            orderID: ID of the order to query (ID as assigned by broker)
            clOrdID (str): Restrict results to given ID
        """
        data = self.request_parser.order(mode="by_id", orderID=orderID, clOrdID=clOrdID)


        # returns ErrorHandlerResult object (OkResult or ErrorResult)
        result = await self.query_private(method="order_info", data=data, retries=retries)

        # if its an error we just want the error message with no parsing
        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            # parse to order response model if error handler has not returned None or ValidationError
            parsed_response = self.response_parser.orders(response=result.value, mode=mode)
            return self.order_validate_and_serialize(mode, parsed_response)



    async def get_open_orders(self,
                              mode: Literal["to_list", "by_id"],
                              symbol: Optional[PAIR] = None,
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

        result = await self.query_private(method="open_orders", data=data, retries=retries)


        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            # parse to order response model if error handler has not returned None or ValidationError
            parsed_response = self.response_parser.orders(response=result.value, symbol=symbol, mode=mode)
            return self.order_validate_and_serialize(mode, parsed_response)




    async def get_closed_orders(self,
                                mode: Literal["to_list", "by_id"],
                                symbol: Optional[PAIR] = None,
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

        result = await self.query_private(method="closed_orders", data=data, retries=retries)
        # parse to order response model and validate
        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.orders(response=result.value, symbol=symbol, mode=mode)
            return self.order_validate_and_serialize(mode, parsed_response)



    # ================================================================================



    def user_trade_validate_and_serialize(self, mode, parsed_response):

        # don't let responsability of validation/serialization to user ==> force it here instead
        mode_to_model = {
            "by_id": TradesByID,
            "to_list": TradesList
        }

        return self.validate_model_from_mode(parsed_response, mode, mode_to_model)



    async def get_user_trades(self,
                              mode: Literal["to_list", "by_id"],
                              symbol: Optional[PAIR] = None,
                              retries: int = 1
                              ):
        data = self.request_parser.trade()

        result = await self.query_private(method="trades_history", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.user_trades(response=result.value, symbol=symbol, mode=mode)
            return self.user_trade_validate_and_serialize(mode, parsed_response)



    async def get_user_trade_by_id(self,
                                   mode: Literal["to_list", "by_id"],
                                   trdMatchID: str,
                                   symbol: Optional[PAIR] = None,
                                   retries: int = 1
                                   ):
        data = self.request_parser.trade(trdMatchID=trdMatchID)

        result = await self.query_private(method="trades_info", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.user_trades(response=result.value, mode=mode)
            return self.user_trade_validate_and_serialize(mode, parsed_response)




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
