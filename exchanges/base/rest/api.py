'''Define Base MetaClass for Exchange Rest APIs'''

from abc import ABC, abstractmethod
import time
import ujson
import logging
import stackprinter
from pydantic import ValidationError
import pandas as pd

from models.data_models.api import Ticker, Ohlc, Orderbook, Trades, Spread, AccountBalance, TradeBalance, OpenOrders


class BaseRestAPI(ABC):
    

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
        '''load all API keys from env file into a deque
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
        return self.env_keys_dq[0][0]

    
    def current_secret(self):
        return self.env_keys_dq[0][1]


    def _nonce(self):
        """ Nonce counter.
        :returns: an always-increasing unsigned integer (up to 64 bits wide)
        """
        return int(1000*time.time())


    def _sign(self, *args, **kwargs):
        raise NotImplementedError
    
    
    
    
    # ================================================================================
    # ================================================================================
    # ==== UTILS


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

    @abstractmethod
    def _load_normalize_map(self):
        '''instantiate instance variable self.pair_map as dict
        Has to map both pairs and assets/currencies

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
        '''input response has to be json string to make it easier to replace values'''
        raise NotImplementedError


    @abstractmethod
    def _handle_response_errors(self, response):
        '''input response has to be json object
        needs to return none if there is an error and the data if there was no error
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
    
    
    
    # ================================================================================
    # ================================================================================
    # ==== USER API QUERIES


    # ========================================
    # ====== Public Methods

    
    @abstractmethod
    async def get_raw_ticker(self, *args, **kwargs) -> dict:
        raise NotImplementedError


    async def get_ticker(self, pair: list, retries: int=0):
        data = await self.get_raw_ticker(pair, retries)
        try: 
            ticker = Ticker(data=data)
            return ticker.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_ticker method returns the correct type")
            logging.error(e)

    

    @abstractmethod
    async def get_raw_ohlc(self, *args, **kwargs) -> list:
        raise NotImplementedError


    async def get_ohlc(self, pair: list, timeframe: int, since: int=None, retries: int=0):
        response = await self.get_raw_ohlc(pair, timeframe, since, retries)
        try: 
            ohlc = Ohlc(data=response["data"], last=response["last"])
            return ohlc.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_ohlc method returns the correct type")
            logging.error(e)


    @abstractmethod
    async def get_raw_orderbook(self, *args, **kwargs) -> dict:
        raise NotImplementedError
    
    
    async def get_orderbook(self, pair: list, count: int=None, retries: int=0):
        response = await self.get_raw_orderbook(pair, count, retries)
        try: 
            ob = Orderbook(asks=response["asks"], bids=response["bids"])
            return ob.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_orderbook method returns the correct type")
            logging.error(e)

    
    @abstractmethod
    async def get_raw_trades(self, *arg, **kwargs) -> dict:
        raise NotImplementedError
    
    
    async def get_trades(self, pair: list, since: int=None, retries: int=0):
        response = await self.get_raw_trades(pair, since, retries)
        try: 
            trades = Trades(data=response["data"], last=response["last"])
            return trades.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_orderbook method returns the correct type")
            logging.error(stackprinter.format(e, style="darkbg2"))


    @abstractmethod
    async def get_raw_spread(self, *args, **kwargs) -> dict:
        raise NotImplementedError
    

    async def get_spread(self, pair: list, since: int=None, retries: int=0):
        """Get spread
        """
        response = await self.get_raw_spread(pair, since, retries)
        try: 
            trades = Spread(data=response["data"], last=response["last"])
            return trades.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_orderbook method returns the correct type")
            logging.error(e)




    # ========================================
    # ====== Private Methods


    @abstractmethod
    async def get_raw_account_balance(self, *args, **kwargs) -> dict:
        raise NotImplementedError
    
    
    async def get_account_balance(self, retries: int=0):
        """Get account balance
        """
        response = await self.get_raw_account_balance(retries)
        try: 
            account_balance = AccountBalance(data=response)
            return account_balance.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_orderbook method returns the correct type")
            logging.error(e)
    
    
    @abstractmethod
    async def get_raw_trade_balance(self, *args, **kwargs) -> pd.DataFrame:
        raise NotImplementedError
    
    
    async def get_trade_balance(self, asset_class: str=None, asset: str=None, retries: int=0):
        """Get trade balance
        """
        response = await self.get_raw_trade_balance(asset_class, asset, retries)
        try: 
            trade_balance = TradeBalance(data=response)
            return trade_balance.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_orderbook method returns the correct type")
            logging.error(e)
    
    
    @abstractmethod
    async def get_raw_open_orders(self, *args, **kwargs) -> pd.DataFrame:
        raise NotImplementedError
    
    async def get_open_orders(self, userref: int=None, trades: bool=True, retries: int=0) -> pd.DataFrame:
        """Get trade balance
        """
        response = await self.get_raw_open_orders(userref, trades, retries)
        try: 
            open_orders = OpenOrders(data=response)
            return open_orders.dict()
        except ValidationError as e:
            logging.warning("Please check that your get_raw_orderbook method returns the correct type")
            logging.error(e)
    
    @abstractmethod
    async def get_closed_orders(self, **kwargs) -> pd.DataFrame:
        raise NotImplementedError


    @abstractmethod
    async def get_user_trades_history(self, **kwargs) -> pd.DataFrame:
        raise NotImplementedError
    
    
    @abstractmethod
    async def get_open_positions(self, **kwargs) -> pd.DataFrame:
        raise NotImplementedError
    
    
    
    # ========================================
    # ====== Private Methods


    @abstractmethod
    async def place_order(self, **kwargs):
        raise NotImplementedError


    @abstractmethod
    async def cancel_order(self, **kwargs):
        raise NotImplementedError


    # @abstractmethod
    # async def cancel_all_orders(self, **kwargs):
    #     raise NotImplementedError


    # @abstractmethod
    # async def close_all_positions(self, **kwargs):
    #     raise NotImplementedError 