"""Lets just copy the file defining base errors from CCXT for now"""

error_hierarchy = {
    'BaseError': {
        'UndefinedError': {},
        'ExchangeError': {
            'AuthenticationError': {
                'PermissionDenied': {},
                'AccountSuspended': {},
                'InvalidSignature': {},
            },
            'ArgumentsRequired': {},
            'BadRequest': {
                'BadSymbol': {},
            },
            'BadResponse': {
                'NullResponse': {},
            },
            'InsufficientFunds': {},
            'InvalidAddress': {
                'AddressPending': {},
            },
            'InvalidOrder': {
                'OrderNotFound': {},
                'OrderNotCached': {},
                'CancelPending': {},
                'OrderImmediatelyFillable': {},
                'OrderNotFillable': {},
                'DuplicateOrderId': {},
            },
            'NotSupported': {},
            'Deprecated': {},
        },
        'NetworkError': {
            'DDoSProtection': {
                'RateLimitExceeded': {},
            },
            'ExchangeNotAvailable': {
                'OnMaintenance': {},
            },
            'InvalidNonce': {},
            'RequestTimeout': {},
        },
    },
}


class BaseError(Exception):

    def __init__(self, raw_error: str, endpoint: str, data: dict):
        self.raw_error = raw_error
        self.exception = self.__class__.__name__
        self.endpoint = endpoint
        self.data = data
        self.accept = True
        self.sleep = None

        msg = f"EXCEPTION:{self.exception}\n{14*' '}Endpoint: {self.endpoint}\n{14*' '}With Arguments: {self.data}"
        super().__init__(msg)


class UndefinedError(BaseError):
    """Meant to catch all exceptions that are not defined in the parser.
    Useful if all error types are not documented, like for Kraken's API.
    (All Noobit exceptions still return the raw unparsed error message)
    """
    pass


class ExchangeError(BaseError):
    pass


class AuthenticationError(ExchangeError):
    pass


class PermissionDenied(AuthenticationError):
    pass


class AccountSuspended(AuthenticationError):
    pass


class InvalidSignature(AuthenticationError):
    pass

class ArgumentsRequired(ExchangeError):
    pass


class BadRequest(ExchangeError):
    pass


class BadSymbol(BadRequest):
    accept = True
    sleep = 10


class BadResponse(ExchangeError):
    pass


class NullResponse(BadResponse):
    pass


class InsufficientFunds(ExchangeError):
    pass


class InvalidAddress(ExchangeError):
    pass


class AddressPending(InvalidAddress):
    pass


class InvalidOrder(ExchangeError):
    pass


class OrderNotFound(InvalidOrder):
    pass


class OrderNotCached(InvalidOrder):
    pass


class CancelPending(InvalidOrder):
    pass


class OrderImmediatelyFillable(InvalidOrder):
    pass


class OrderNotFillable(InvalidOrder):
    pass


class DuplicateOrderId(InvalidOrder):
    pass


class NotSupported(ExchangeError):
    pass


class Deprecated(ExchangeError):
    pass


class NetworkError(BaseError):
    pass


class DDoSProtection(NetworkError):
    accept = False
    sleep = 60

class RateLimitExceeded(DDoSProtection):
    accept = False
    sleep = 60


class ExchangeNotAvailable(NetworkError):
    accept = False
    sleep = 60


class OnMaintenance(ExchangeNotAvailable):
    pass


class InvalidNonce(NetworkError):
    pass


class RequestTimeout(NetworkError):
    accept = False
    sleep = 60


__all__ = [
    'error_hierarchy',
    'UndefinedError',
    'ExchangeError',
    'AuthenticationError',
    'PermissionDenied',
    'AccountSuspended',
    'InvalidSignature',
    'ArgumentsRequired',
    'BadRequest',
    'BadSymbol',
    'BadResponse',
    'NullResponse',
    'InsufficientFunds',
    'InvalidAddress',
    'AddressPending',
    'InvalidOrder',
    'OrderNotFound',
    'OrderNotCached',
    'CancelPending',
    'OrderImmediatelyFillable',
    'OrderNotFillable',
    'DuplicateOrderId',
    'NotSupported',
    'Deprecated',
    'NetworkError',
    'DDoSProtection',
    'RateLimitExceeded',
    'ExchangeNotAvailable',
    'OnMaintenance',
    'InvalidNonce',
    'RequestTimeout'
]


# ================================================================================



# FIX Protocol Error Messages

ERROR = {

    1: "User Identification is not correct",
    2: "Protocol Version is not supported",
    3: "Message Type is not supported",
    4: "Session ID is not active",
    6: "Message Type requested is not supported",
    8: "Message is too short",
    9: "Message is too long",
    10: "Message contains Binary Data",
    11: "No Heartbeat Activity: Disconnection",
    12: "Message Type is Out Of Context",
    13: "User ID has been deactivated: Disconnection",
    14: "Syntax Error + <detailed text>",
    15: "Field value is too small",
    16: "Field value is too big",
    100: "Firm is Forbidden to trade on this Group",
    101: "Duration Type is Forbidden for current Group state",
    102: "Verb field (Side) cannot be modified",
    103: "Order is not active",
    104: "Price Type is forbidden for this instrument",
    105: "Price Term is Forbidden for current Instrument state",
    108: "Duration Type is Forbidden for current Instrument state",
    109: "Order cannot be processed: No opposite limit",
    110: "Price does not represent a valid tick increment for this Instrument",
    111: "Duration Type is invalid for this Price Type",
    112: "Cross Order price must be within the Instrument trading limits",
    113: "Cross Order price is outside bid/ask price spread",
    114: "Opposite firm must be filled for committed order",
    116: "Cross order is not allowed",
    117: "Cross order quantity is outside limits",
    118: "Duration Type Is Invalid For This Price Term",
    119: "Cross order notional value is outside limits",
    120: "Disclosed Notional value is below the instrument threshold",
    121: "Order Notional value is outside the instrument thresholds",
    122: "Physical Leg must be filled for this type of order",
    123: "Trade has already been approved",
    124: "Order from Account type House cannot have Client Id Code",
    125: "Investment decision code is missing",
    126: "Client Identification is missing",
    201: "GTD date must be equal to or greater than current day",
    202: "GTD date must be equal to or less than Instrument expiration date",
    203: "GTD date must be filled only if Duration Type is equal to GTD",
    300: "Quantity Term is Forbidden for current Instrument state",
    302: "Quantity must be less than or equal to Maximum Improvement Quantity",
    303: "Quantity Term is not authorized for this Order Type",
    304: "Additional Quantity must be less than Order Quantity",
    305: "Additional Quantity is too small",
    306: "Minimum quantity cannot be modified",
    307: "Quantity Term is forbidden for Duration Type",
    308: "Order quantity is outside the instrument quantity threshold",
    309: "Quantities must be multiples of lot size",
    402: "Trader ID field cannot be modified",
    403: "Market Maker not authorized for Group",
    500: "Order price is outside the instrument price threshold",
    501: "Price field is mandatory for Limit Orders",
    502: "Price field must not be filled for this Price Type",
    503: "Order cannot be modified or cancelled",
    504: "Additional Price is forbidden for Price Term",
    505: "Order price must be greater than additional price",
    506: "Order price must be lower than additional price",
    507: "Additional price must be lower than last price or last day price",
    508: "Additional price must be greater than last price or last day price",
    509: "Order rejected. Cannot trade outside instrument price thresholds.",
    510: "Order cannot be modified",
    511: "Order price is outside circuit breaker limits",
    # 512 Price Term Invalid For Price Type
    # 700 Only one quote per Instrument and per Side is accepted
    # 701 Quote is not present in the Instrument Book
    # 702 Market Maker Protection in progress; Quote not processed.
    # 703 Advanced Market Maker Protection not enabled for this Group
    # 704 Buy and Sell must not cross for the same instrument
    # 705 Number of quotes is not in sync with the message length
    # 707 Market Maker Protection state must be re-activated
    # 708 Trader ID has no quote for this Group
    # 709 All the Instruments must belong to the same Group
    # 710 Clearing Data has not been initialized
    # 1000 Cross orders forbidden in Pre-opening phase.
    # 1001 Instrument does not exist
    # 1002 Group ID does not exist
    # 1003 Trader ID is invalid
    # 1004 Message Type is forbidden for current Instrument state
    # 1007 Participant must use A4 protocol version
    # 1008 RFQ currently underway for this instrument
    # 1009 Action not allowed under current configuration
    # 1010 Number of entries is invalid
    # 1107 Firm or trader had been disabled
    # 1108 Instrument mandatory when using MM Monitoring mode forced
    # 1109 Market maker has no obligation for this group
    # 1110 Participant not authorized for this Group (for Execution Report [MsgType 35 = 8])
    # 1111 Participant not authorized for this Account Type (for Execution Report [MsgType 35 = 8])
    # 2000 Technical error; function not performed. Contact Technical Help Desk.
    # 2001 Gateway State forbids this command. Contact Technical Help Desk.
    # 2002 Function only partially performed. Contact Technical Help Desk.
    # 3017 Open Close Missing Invalid
    # 3041 Unknown Clearing Operation Mode
    # 3042 Invalid Price Type
    # 3100 Order Quantity Limit exceeded at the trader/instrument level
    # 3101 TradedLong limit exceeded at the trader/instrument level
    # 3102 TradedShort limit exceeded at the trader/instrument level
    # 3103 ExposedLong limit exceeded at the trader/instrument level
    # 3104 ExposedShort limit exceeded at the trader/instrument level
    # 3107 Order Value limit exceeded at trader/instrument level
    # 3108 Order Price outside High/Low limits at trader/instrument level
    # 3110 Order Quantity Limit exceeded at the trader/group level
    # 3111 TradedLong limit exceeded at the trader/group level
    # 3112 TradedShort limit exceeded at the trader/group level
    # 3113 ExposedLong limit exceeded at the trader/group level
    # 3114 ExposedShort limit exceeded at the trader/group level
    # 3115 TradedSpreads limit exceeded at the trader/group level
    # 3116 ExposedSpreads limit exceeded at the trader/group level
    # 3117 Order Value limit exceeded at the trader/group level
    # 3120 Order Quantity Limit exceeded at the Firm/instrument level
    # 3121 TradedLong limit exceeded at the firm/instrument level
    # 3122 TradedShort limit exceeded at the firm/instrument level
    # 3123 ExposedLong limit exceeded at the firm/instrument level
    # 3124 ExposedShort limit exceeded at the firm/instrument level
    # 3127 Order value limit exceeded at the firm/instrument level
    # 3128 Order Price outside High/Low limits at the firm/instrument level
    # 3130 Order Quantity Limit exceeded at the firm/group level
    # 3131 TradedLong limit exceeded at the firm/group level
    # 3132 TradedShort limit exceeded at the firm/group level
    # 3133 ExposedLong limit exceeded at the firm/group level
    # 3134 ExposedShort limit exceeded at the firm/group level
    # 3135 TradedSpreads limit exceeded at the firm/group level
    # 3136 ExposedSpreads limit exceeded at the trader/group level
    # 3137 Order Value limit exceeded at the firm/group level
    # 9017 Invalid number of legs
    # 9018 Invalid leg information
    # 9019 Unknown strategy type
    # 9020 Firm creation quota has been reached
    # 9021 Leg instrument is not active
    # 9022 Strategy has unpriced legs
    # 9023 Group state does not allow this function

}