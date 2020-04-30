from noobit.models.data.base.errors import *

# see: https://support.kraken.com/hc/en-us/articles/360001491786-API-Error-Codes
map_errors = {

        # Errors related to rate limits
        'EOrder:Rate limit exceeded': DDoSProtection,
        'EGeneral:Temporary lockout': DDoSProtection,
        'EAPI:Rate limit exceeded': RateLimitExceeded,

        # General usage errors
        'EQuery:Unknown asset pair': BadSymbol,
        'EGeneral:Invalid arguments': BadSymbol,
        'EGeneral:Internal error': ExchangeNotAvailable,
        'EGeneral:Permission denied': PermissionDenied,
        'EAPI:Invalid key': AuthenticationError,
        'EAPI:Invalid signature': InvalidSignature,
        'EAPI:Invalid nonce': InvalidNonce,
        'EAPI:Feature disabled': Deprecated,

        # Service status errors
        'EService:Unavailable': ExchangeNotAvailable,
        'EService:Busy': ExchangeNotAvailable,

        # Trading errors
        'ETrade:Locked': Exception,

        # Order placing errors
        'EOrder:Cannot open position': Exception,
        'EOrder:Cannot open opposing position': Exception,
        'EOrder:Margin allowance exceeded': Exception,
        'EOrder:Insufficient margin': Exception,
        'EOrder:Insufficient funds': InsufficientFunds,
        'EOrder:Order minimum not met': Exception,
        'EOrder:Orders limit exceeded': Exception,
        'EOrder:Positions limit exceeded': Exception,
        'EOrder:Trading agreement required': Exception,

        # Network timeout errors

        # Not documented by Kraken
        'EOrder:Invalid order': OrderNotFound
        # 'EQuery:Invalid asset pair': BadSymbol,  # {"error":["EQuery:Invalid asset pair"]}
        # 'EFunding:Unknown withdraw key': ExchangeError,
        # 'EFunding:Invalid amount': InsufficientFunds,
        # 'EDatabase:Internal error': ExchangeNotAvailable,
        # 'EQuery:Unknown asset': ExchangeError,
        # # Exceptions not defined by CCXT
}


def handle_error_messages(response, endpoint, data):

    if not response:
        return BadResponse(raw_error=None, endpoint=endpoint, data=data)

    if response["error"]:

        # kraken error message is a list:  example response: {'error': ['EGeneral:Invalid arguments', ]}
        [kraken_error_msg] = response["error"]
        noobit_error = map_errors.get(kraken_error_msg, UndefinedError)(raw_error=kraken_error_msg, endpoint=endpoint, data=data)
        return {
            "accept": noobit_error.accept,
            # "value": {
            #     "endpoint": noobit_error.endpoint,
            #     "data": noobit_error.data,
            #     "sleep": noobit_error.sleep
            # },
            "value": noobit_error
        }
        # how do we handle the variable sleep time (for ex long sleep for rate limit)
        # ONE EXAMPLE :
        #   REPLACE     'EOrder:Rate limit exceeded': DDoSProtection
        #   WITH        'EOrder:Rate limit exceeded': {"err": DDoSProtection, "sleep": 60}
        # then in main file we will do:
        #   handler = response_parser.errors(response)
        #   logging.error(handler["err"])
        #   await asyncio.sleep(handler["sleep"])
    else:
        return {"accept": True, "value": response["result"]}