from abc import ABC, abstractmethod


class APIAbc(ABC):


    # ================================================================================
    # ==== AUTHENTICATION
    # ================================================================================


    @abstractmethod
    def _load_all_env_keys(self):
        '''Load all API keys from env file into a deque.

        Notes:
            In .env file, keys should contain :
                API Key : <exchange-name> & "key"
                API Secret : <exchange-name> & "secret"
        '''
        raise NotImplementedError



    @abstractmethod
    def _sign(self, data: dict, urlpath: str):
        raise NotImplementedError




    # ================================================================================
    # ==== UTILS
    # ================================================================================


    @abstractmethod
    def _load_normalize_map(self):
        '''Instantiate instance variable self.pair_map as dict.

        keys : exchange format
        value : standard format

        eg for kraken : {"XXBTZUSD": "XBT-USD", "ZUSD": "USD"}
        '''
        raise NotImplementedError



    @abstractmethod
    def _load_pair_specs_map(self):
        '''Instantiate instance variable self.pair_info as dict.

        keys : exchange format
        value : standard format

        eg for kraken : {"XBT-USD": {"price_decimals": 0.1, "volume_decimals": 0.1}}
        '''
        raise NotImplementedError



    @abstractmethod
    async def _handle_response_errors(self, response):
        '''Input response has to be json object.
        Needs to return none if there is an error and the data if there was no error.
        '''
        raise NotImplementedError
