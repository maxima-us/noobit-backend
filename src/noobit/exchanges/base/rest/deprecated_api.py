'''
Define Base Class for Exchange Rest API.
Exchange Rest API Class must inherit from both Base Class and Abstract Base Class
'''
from abc import ABC, abstractmethod
import time
import asyncio
from collections import deque
from typing import Optional, Union, Any, Dict
from typing_extensions import Literal

import ujson
import stackprinter
from pydantic import BaseModel, ValidationError
import pandas as pd
from starlette import status

# general
from noobit.server import settings
from noobit.logger.structlogger import get_logger, log_exception, log_exc_to_db

# models
from noobit.models.data.base.types import PAIR, TIMEFRAME, TIMESTAMP
from noobit.models.data.base.errors import ErrorHandlerResult, BaseError, OKResult, ErrorResult
from noobit.models.data.base.response import NoobitResponse, OKResponse, ErrorResponse
from noobit.models.data.response.order import OrdersList, OrdersByID
from noobit.models.data.response.trade import TradesList, TradesByID
from noobit.models.data.response.ohlc import Ohlc
from noobit.models.data.response.orderbook import OrderBook
from noobit.models.data.response.instrument import Instrument
from noobit.models.data.response.balance import Balances
from noobit.models.data.response.exposure import Exposure

# parsers
from noobit.models.data.request.parse.base import BaseRequestParser
from noobit.models.data.response.parse.base import BaseResponseParser


from noobit.models.data.request import (
    OhlcRequest, TradesRequest,
    OrderBookRequest, InstrumentRequest, OrdersRequest
)


logger = get_logger(__name__)


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

        # FIXME we need to keep track of nonces so we dont run into errors because of async
        # verify that current  last, similar to Hummingbot
        self.last_nonce = None


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
            log_exception(logger, e)

    def current_key(self):
        """env key we are currently using"""
        try:
            return self.env_keys_dq[0][0]
        except Exception as e:
            log_exception(logger, e)


    def current_secret(self):
        """env secret we are currently using"""
        try:
            return self.env_keys_dq[0][1]
        except Exception as e:
            log_exception(logger, e)


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
            log_exception(logger, e)
            await log_exc_to_db(logger, e)

        # try:
        #     logging.warning(result)
        #     # validated_result = ErrorHandlerResult(**result)
        #     validated_result = OKResult(result.dict())
        # except ValidationError as e:
        #     logging.error(e)
        #     return ErrorResult(accept=True, value=str(e))
        if not isinstance(result, ErrorHandlerResult):
            error_msg = "Invalid Type: Result needs to be ErrorResult or OKResult"
            logger.error(error_msg)
            return ErrorResult(accept=True, value=error_msg)


        # if isinstance(validated_result.value, BaseError):
        if not result.is_ok:
            # result["value"] returns one of our custom error classes here
            # exception = result.value
            logger.error(result.value)

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
            #TODO this stops the whole server, find better way to return a server side error
            self.response.raise_for_status()

        logger.debug(f"API Request URL: {self.response.url}")

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

        # if not self.current_key() or not self.current_secret():
        #     raise Exception('Either key or secret is not set! (Use `load_key()`.')

        if not self.current_key() or not self.current_secret():
            logger.error('Either key or secret is not set!')
            # settings.SERVER.should_exit = True
            result = ErrorResult(accept=True, status_code=400, value="Either key or secret is not set")
            return result


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

            validated = pydantic_model(**parsed_response)
            defined_fields = list(validated.dict().keys())

            # handle different cases, where we define data only, or multiple fields
            if defined_fields == ["data"]:
                value = validated.dict()["data"]
            else:
                value = validated.dict()

            return OKResponse(status_code=status.HTTP_200_OK,
                              value=value
                              )

        except ValidationError as e:
            logger.error(str(e))
            return ErrorResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                 value=e.errors()
                                 )


    def validate_params(self,
                        model: BaseModel,
                        **kwargs)-> ErrorHandlerResult:
        try:
            params = model(**kwargs)
            return OKResult(value=params.dict())
        except ValidationError as e:
            logger.error(str(e))
            return ErrorResult(value=e.errors(), accept=True)
        except Exception as e:
            logger.error(str(e))
            return ErrorResult(value=e.errors(), accept=True)


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
        #TODO validate kwargs by passing them to OhlcParameters Pydantic Model
        params = self.validate_params(model=OhlcRequest, symbol=symbol, timeframe=timeframe)
        if params.is_error:
            return ErrorResponse(status_code=400, value=params.value)

        # TODO Handle request errors (for ex if we pass invalid symbol, or pair that does not exist)
        try:
            data = self.request_parser.ohlc(symbol=params.value["symbol"], timeframe=params.value["timeframe"])
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        # data = self.request_parser.ohlc(symbol=symbol.upper(), timeframe=timeframe)
        # if isinstance(data, BaseException):
        #     return ErrorResponse(status_code=400, value=data)

        #! vvvvvvvvvvvvvvvvvvvvvvv HANDLE REQUEST PARSING ERRORS
        # make request parser return a RequestResult object
        # but this leaves responsability to the user, which is bad
        # ==> Basic Example:
        # if request.is_error:
        #   return ErrorResponse(status_code=bad_request, value=request.value)

        result = await self.query_public(method="ohlc", data=data, retries=retries)
        # parse to order response model and validate
        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.ohlc(response=result.value)
            # not all pydantic models have <data> as only field
            # so we need to specify the field here to make it work for all models
            return self.ohlc_validate_and_serialize({"data": parsed_response})


    async def get_ohlc_as_pandas(self,
                                 symbol: PAIR,
                                 timeframe: TIMEFRAME,
                                 retries: int = 1,
                                 ) -> NoobitResponse:
        response = await self.get_ohlc(symbol, timeframe, retries)

        if response.is_ok:
            cols = ["symbol", "utcTime", "open", "high", "low", "close", "volume", "vwap", "trdCount"]
            df = pd.DataFrame(data=response.value, columns=cols)
            response.value = df
            return response
        else:
            # response is ErrorResponse and we return it in full
            return response



    # ================================================================================


    def public_trade_validate_and_serialize(self, parsed_response):

        mode_to_model = {
            "public_trade": TradesList
        }

        return self.validate_model_from_mode(parsed_response, mode="public_trade", mode_to_model=mode_to_model)


    async def get_public_trades(self,
                                symbol: PAIR,
                                since: TIMESTAMP = None,
                                retries: int = 1
                                ) -> NoobitResponse:
        """Get data on public trades. Response value is a list with each item being a dict that
        corresponds to the data for a single trade.
        """
        params = self.validate_params(model=TradesRequest, symbol=symbol, since=since)
        if params.is_error:
            return ErrorResponse(status_code=400, value=params.value)

        try:
            data = self.request_parser.public_trades(symbol=params.value["symbol"], since=params.value["since"])
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        result = await self.query_public(method="trades", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.trades(response=result.value)
            # not all pydantic models have <data> as only field
            # so we need to specify the field here to make it work for all models
            return self.public_trade_validate_and_serialize({"data": parsed_response["data"], "last": parsed_response["last"]})


    async def get_public_trades_as_pandas(self,
                                          symbol: PAIR,
                                          retries: int = 1,
                                          ) -> NoobitResponse:
        response = await self.get_public_trades(symbol, retries=retries)

        if response.is_ok:
            df = pd.DataFrame(data=response.value["data"])
            response.value = df
            return response
        else:
            # response is ErrorResponse and we return it in full
            return response




    # ================================================================================


    def orderbook_validate_and_serialize(self, parsed_response):

        mode_to_model = {
            "orderbook": OrderBook
        }

        return self.validate_model_from_mode(parsed_response, mode="orderbook", mode_to_model=mode_to_model)



    async def get_orderbook(self,
                            symbol: PAIR,
                            retries: int = 1,
                            ) -> NoobitResponse:
        """
        """
        params = self.validate_params(model=OrderBookRequest, symbol=symbol)
        if params.is_error:
            return ErrorResponse(status_code=400, value=params.value)

        try:
            data = self.request_parser.orderbook(params.value["symbol"])
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        result = await self.query_public(method="orderbook", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.orderbook(response=result.value)
            return self.orderbook_validate_and_serialize(parsed_response)


    async def get_orderbook_as_pandas(self,
                                      symbol: PAIR,
                                      retries: int = 1,
                                      ) -> NoobitResponse:
        response = await self.get_orderbook(symbol, retries=retries)

        if response.is_ok:
            asks_df = pd.DataFrame.from_dict(response.value["asks"], orient="index")
            bids_df = pd.DataFrame.from_dict(response.value["bids"], orient="index")
            response.value = {"asks": asks_df, "bids": bids_df}
            return response
        else:
            # response is ErrorResponse and we return it in full
            return response


    # ================================================================================


    def instrument_validate_and_serialize(self, parsed_response):

        mode_to_model = {
            "instrument": Instrument
        }

        return self.validate_model_from_mode(parsed_response, mode="instrument", mode_to_model=mode_to_model)


    async def get_instrument(self,
                             symbol: PAIR,
                             retries: int = 1,
                             ) -> NoobitResponse:
        """Get data for instrument. Depending on exchange this will aggregate ticker, spread data
        """
        params = self.validate_params(model=InstrumentRequest, symbol=symbol)
        if params.is_error:
            return ErrorResponse(status_code=400, value=params.value)

        try:
            data = self.request_parser.instrument(params.value["symbol"])
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        result = await self.query_public(method="instrument", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.instrument(response=result.value)
            return self.instrument_validate_and_serialize(parsed_response)




    # ================================================================================
    # ====== PRIVATE REQUESTS
    # ================================================================================



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
                        symbol = None,
                        retries: int = 1
                        ) -> Union[list, dict, str]:
        """Get a single order
            mode (str): Parse response to list, or index by order id
            orderID: ID of the order to query (ID as assigned by broker)
            clOrdID (str): Restrict results to given ID
        """
        try:
            data = self.request_parser.orders(mode="by_id", orderID=orderID, clOrdID=clOrdID)
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        # returns ErrorHandlerResult object (OkResult or ErrorResult)
        result = await self.query_private(method="order_info", data=data, retries=retries)

        # if its an error we just want the error message with no parsing
        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            # parse to order response model if error handler has not returned None or ValidationError
            parsed_response = self.response_parser.orders(response=result.value, mode=mode)
            # not all pydantic models have <data> as only field
            # so we need to specify the field here to make it work for all models
            return self.order_validate_and_serialize(mode, {"data": parsed_response})



    async def get_open_orders(self,
                              mode: Literal["to_list", "by_id"],
                              symbol: Optional[PAIR] = None,
                              clOrdID: Optional[int] = None,
                              orderID = None,
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
        if symbol is not None:
            symbol = symbol.upper()

        try:
            data = self.request_parser.orders("open", symbol=symbol, clOrdID=clOrdID)
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        result = await self.query_private(method="open_orders", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            # parse to order response model if error handler has not returned None or ValidationError
            parsed_response = self.response_parser.orders(response=result.value, symbol=symbol, mode=mode)
            # not all pydantic models have <data> as only field
            # so we need to specify the field here to make it work for all models
            return self.order_validate_and_serialize(mode, {"data": parsed_response})



    async def get_open_orders_as_pandas(self,
                                          symbol: Optional[PAIR] = None,
                                          retries: int = 1
                                        ):
        response = await self.get_open_orders("by_id", symbol, retries=retries)

        if response.is_ok:
            df = pd.DataFrame.from_dict(response.value, orient="index")
            response.value = df
            return response
        else:
            # response is ErrorResponse and we return it in full
            return response



    async def get_closed_orders(self,
                                mode: Literal["to_list", "by_id"],
                                symbol: Optional[PAIR] = None,
                                clOrdID: Optional[int] = None,
                                orderID = None,
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

        if symbol is not None:
            symbol = symbol.upper()

        try:
            data = self.request_parser.orders("closed", symbol=symbol, clOrdID=clOrdID)
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        result = await self.query_private(method="closed_orders", data=data, retries=retries)
        # parse to order response model and validate
        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.orders(response=result.value, symbol=symbol, mode=mode)
            # not all pydantic models have <data> as only field
            # so we need to specify the field here to make it work for all models
            return self.order_validate_and_serialize(mode, {"data": parsed_response})



    async def get_closed_orders_as_pandas(self,
                                          symbol: Optional[PAIR] = None,
                                          retries: int = 1
                                        ):
        response = await self.get_closed_orders("by_id", symbol, retries=retries)

        if response.is_ok:
            df = pd.DataFrame.from_dict(response.value, orient="index")
            response.value = df
            return response
        else:
            # response is ErrorResponse and we return it in full
            return response




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

        try:
            data = self.request_parser.user_trades()
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        result = await self.query_private(method="trades_history", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.user_trades(response=result.value, symbol=symbol, mode=mode)
            # not all pydantic models have <data> as only field
            # so we need to specify the field here to make it work for all models
            return self.user_trade_validate_and_serialize(
                mode, {"data": parsed_response["data"], "last": parsed_response["last"]}
            )



    async def get_user_trades_as_pandas(self,
                                        symbol: Optional[PAIR] = None,
                                        retries: int = 1
                                        ):
        response = await self.get_user_trades("by_id", symbol, retries)

        if response.is_ok:
            df = pd.DataFrame.from_dict(response.value, orient="index")
            response.value = df
            return response
        else:
            # response is ErrorResponse and we return it in full
            return response



    async def get_user_trade_by_id(self,
                                   mode: Literal["to_list", "by_id"],
                                   trdMatchID: str,
                                   symbol: Optional[PAIR] = None,
                                   retries: int = 1
                                   ):
        """Get info on a single trade
        """
        try:
            data = self.request_parser.user_trades(trdMatchID=trdMatchID)
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        result = await self.query_private(method="trades_info", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.user_trades(response=result.value, mode=mode)
            # not all pydantic models have <data> as only field
            # so we need to specify the field here to make it work for all models
            return self.user_trade_validate_and_serialize(mode, {"data": parsed_response})



    # ================================================================================



    def positions_validate_and_serialize(self, mode, parsed_response):

        # don't let responsability of validation/serialization to user ==> force it here instead
        mode_to_model = {
            "by_id": OrdersByID,
            "to_list": OrdersList
        }

        return self.validate_model_from_mode(parsed_response, mode, mode_to_model)



    async def get_open_positions(self,
                                 mode: Literal["to_list", "by_id"],
                                 symbol: Optional[PAIR] = None,
                                 retries: int = 1
                                 ) -> NoobitResponse:
        """For kraken there is no <closed positions> endpoint, but we can simulate it by querying <closed orders> and then filtering for margin orders
        Or even better filter out <trades history> and <type==closed position>
        """
        if symbol is not None:
            symbol = symbol.upper()

        try:
            data = self.request_parser.open_positions(symbol)
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        result = await self.query_private(method="open_positions", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.open_positions(response=result.value, mode=mode)
            # not all pydantic models have <data> as only field
            # so we need to specify the field here to make it work for all models
            return self.positions_validate_and_serialize(mode, {"data": parsed_response})


    async def get_open_positions_as_pandas(self,
                                           symbol: Optional[PAIR] = None,
                                           retries: int = 1
                                           ) -> NoobitResponse:
        response = await self.get_open_positions("by_id", symbol, retries)

        if response.is_ok:
            df = pd.DataFrame.from_dict(response.value, orient="index")
            response.value = df
            return response
        else:
            # response is ErrorResponse and we return it in full
            return response


    # for some exchanges there are not direct endpoints to get closed positions, so we need to work around it
    async def get_closed_positions(self,
                                   mode: Literal["to_list", "by_id"],
                                   symbol: Optional[PAIR] = None,
                                   retries: int = 1
                                   ) -> NoobitResponse:

        if symbol is not None:
            symbol = symbol.upper()

        try:
            data = self.request_parser.closed_positions(symbol)
        except Exception as e:
            msg = repr(e)
            logger.error(msg)
            await log_exc_to_db(logger, e)
            return ErrorResponse(status_code=400, value=msg)

        result = await self.query_private(method="closed_positions", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.closed_positions(response=result.value, mode=mode)
            return self.positions_validate_and_serialize(mode, {"data": parsed_response})



    async def get_closed_positions_as_pandas(self,
                                             symbol: Optional[PAIR] = None,
                                             retries: int = 1
                                             ) -> NoobitResponse:
        response = await self.get_closed_positions("by_id", symbol, retries)

        if response.is_ok:
            df = pd.DataFrame.from_dict(response.value, orient="index")
            response.value = df
            return response
        else:
            # response is ErrorResponse and we return it in full
            return response

    # ================================================================================



    def balances_validate_and_serialize(self, parsed_response):
        # don't let responsability of validation/serialization to user ==> force it here instead
        mode_to_model = {
            "balances": Balances,
        }

        return self.validate_model_from_mode(parsed_response, "balances", mode_to_model)


    async def get_balances(self,
                           symbol: Optional[PAIR] = None,
                           retries: int = 1
                           ) -> NoobitResponse:
        if symbol is not None:
            symbol = symbol.upper()
        data = {}

        result = await self.query_private(method="balances", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.balances(response=result.value)
            return self.balances_validate_and_serialize({"data": parsed_response})



    # ================================================================================


    def exposure_validate_and_serialize(self, parsed_response):
        # don't let responsability of validation/serialization to user ==> force it here instead
        mode_to_model = {
            "exposure": Exposure,
        }

        return self.validate_model_from_mode(parsed_response, "exposure", mode_to_model)



    async def get_exposure(self,
                           retries: int = 1):

        data = {}
        result = await self.query_private(method="exposure", data=data, retries=retries)

        if not result.is_ok:
            return ErrorResponse(status_code=result.status_code, value=result.value)
        else:
            parsed_response = self.response_parser.exposure(response=result.value)
            return self.exposure_validate_and_serialize(parsed_response)





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

        #! Do not forget to quantize decimal places to exchange supported format
        # pair = pair[0].upper()

        # try:
        #     price_decimals = Decimal(self.exchange_pair_specs[pair]["price_decimals"])
        #     price = Decimal(price).quantize(10**-price_decimals)

        #     if price2:
        #         price2 = Decimal(price2).quantize(10**-price_decimals)

        #     volume_decimals = Decimal(self.exchange_pair_specs[pair]["volume_decimals"])
        #     volume = Decimal(volume).quantize(10**-volume_decimals)

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
        response = await self.get_open_orders(mode="by_id", retries=retries)
        open_orders = response.value
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



