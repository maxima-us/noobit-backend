from typing import List, Any, Dict, Tuple, Optional, Union
from typing_extensions import Literal
from datetime import date
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel



# ========================================
# ====== DATA

class Timestamp(BaseModel):
    data : Decimal

class Price(BaseModel):
    data : Decimal

class Volume(BaseModel):
    data : Decimal




# ========================================
# ====== TICKER


class TickerItem(BaseModel):
    """Ticker Model
    """

    ask: List[Decimal]
    bid: List[Decimal]
    open: Decimal
    high: List[Decimal]
    low: List[Decimal]
    close: List[Decimal]
    volume: List[Decimal]
    vwap: List[Decimal] = None
    trades: List[Decimal] = None


class Ticker(BaseModel):
    
    data: Dict[str, TickerItem]

    class Config:
        arbitrary_types_allowed = True




# ========================================
# ====== OHLC


class OhlcItem(BaseModel):
    """
    <time>, <open>, <high>, <low>, <close>, <vwap>, <volume>, <count>
    """
    time : Decimal
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal 
    vwap: Decimal = None
    count: Decimal = None


class Ohlc(BaseModel):
    """
    array of <time>, <open>, <high>, <low>, <close>, <vwap>, <volume>, <count>
    vwap and count can be none
    """

    # data : List[OhlcItem]
    # last : Decimal

    data: List[Tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Optional[Decimal], Decimal, Optional[Decimal]]] 


    class Config:
        arbitrary_types_allowed = True




# ========================================
# ====== Orderbook


class OrderbookItem(BaseModel):
    """
    <price>, <volume>, <timestamp>
    """
    # data: Tuple[Price, Volume, Timestamp]
    
    # class Config:
    #     arbitrary_types_allowed = True

    price: Decimal
    volume: Decimal
    timestamp: Decimal


class Orderbook(BaseModel):
    """
    array of <price>, <volume>, <timestamp>
    """

    asks: List[Tuple[Decimal, Decimal, Decimal]]
    bids: List[Tuple[Decimal, Decimal, Decimal]]
    # bids: List[OrderbookItem]

    class Config:
        arbitrary_types_allowed = True




# ========================================
# ====== Trades


class TradesItem(BaseModel):
    """
    array of array entries
    (<price>, <volume>, <time>, <buy/sell>, 
    <market/limit>, <miscellaneous>)
    """

    price: Decimal
    volume: Decimal
    time: Decimal
    side: str
    type: str
    misc: Any = None 


class OrderSide(str, Enum):
    buy: "b"
    sell: "s"


class OrderType(str, Enum):
    market: "m"
    limit: "l"


class Trades(BaseModel):
    """
    array of array entries
    (<price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>)
    """

    # data = List[Tuple[Decimal, Decimal, Decimal, Literal["b", "s"], Literal["m", "l"], Optional[Any]]]
    data = List[Tuple[Decimal, Decimal, Decimal, Any, Any, Optional[Any]]]
    last = Decimal

    class Config:
        arbitrary_types_allowed = True




# ========================================
# ====== Spread


class SpreadItem(BaseModel):
    """
    array of array entries(<time>, <bid>, <ask>)
    """
    time: Decimal
    bid: Decimal
    ask: Decimal


class Spread(BaseModel):
    data: List[Tuple[Decimal, Decimal, Decimal]]
    last: Decimal

    class Config:
        arbitrary_types_allowed = True




# ========================================
# ====== Account Balance


class AccountBalance(BaseModel):
    # tortoise ORM can not json serialize Decimal
    data: Dict[str, float]




# ========================================
# ====== Account Balance


class TradeBalance(BaseModel):
    # tortoise ORM can not json serialize Decimal
    data: Dict[str, float]




# ========================================
# ====== Account Balance


class OpenOrdersItem(BaseModel):
    """
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
    refid: str
    userref: str
    status: Union["pending", "open", "closed", "canceled", "expired"]
    opentm: Decimal
    starttm: Decimal
    expiretm: Decimal
    descr: dict
    vol: Decimal
    vol_exec: Decimal
    cost: Decimal
    fee: Decimal
    price: Optional[Decimal]
    stopprice: Optional[Decimal]
    limitprice: Optional[Decimal]
    misc: Any
    oflags: Any
    trades: Any

class OpenOrders(BaseModel):
    # tortoise ORM can not json serialize Decimal
    data: Dict[str, OpenOrdersItem]
