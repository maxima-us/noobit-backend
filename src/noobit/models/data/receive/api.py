from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

from typing_extensions import Literal, TypedDict
from pydantic import BaseModel



# ========================================
# ====== DATA





# ========================================
# ====== TICKER


class TickerItem(TypedDict):
    """Ticker Data Model
    """

    ask: Tuple[Decimal, Decimal, Decimal]
    bid: Tuple[Decimal, Decimal, Decimal]
    open: Decimal
    high: Tuple[Decimal, Decimal]
    low: Tuple[Decimal, Decimal]
    close: Tuple[Decimal, Decimal]
    volume: Tuple[Decimal, Decimal]
    vwap: Tuple[Decimal, Decimal] = None
    trades: Tuple[Decimal, Decimal] = None


class Ticker(BaseModel):
    """Ticker Data Model

    Args:
        data (dict) : dictionary of format {pair:tickerinfo}
            tickerinfo: TypedDict with keys:
                ask, bid, open, high, low, close, volume, vwap, trades
    """

    data: Dict[str, TickerItem]

    class Config:
        arbitrary_types_allowed = True




# ========================================
# ====== OHLC


OhlcEntry = Tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Optional[Decimal], Decimal, Optional[Decimal]]


class Ohlc(BaseModel):
    """OHLC Data Model

    Args:
        data (list) : array of <time>, <open>, <high>, <low>, <close>, <vwap>, <volume>, <count>
            vwap and count are optional, can be none
        last (Decimal) : id to be used as since when polling for new, committed OHLC data
    """

    data: List[OhlcEntry]
    last: Decimal

    # data: List[Tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Optional[Decimal], Decimal, Optional[Decimal]]]
    # last: Decimal


    class Config:
        arbitrary_types_allowed = True




# ========================================
# ====== Orderbook


OrderbookEntry = Tuple[Decimal, Decimal, Decimal]


class Orderbook(BaseModel):
    """OrderBook Data Model

    Args:
        asks (list) : array of <price>, <volume>, <timestamp>
        bids (list) : array of <price>, <volume>, <timestamp>
    """

    # asks: List[Tuple[Decimal, Decimal, Decimal]]
    # bids: List[Tuple[Decimal, Decimal, Decimal]]
    asks: List[OrderbookEntry]
    bids: List[OrderbookEntry]

    class Config:
        arbitrary_types_allowed = True




# ========================================
# ====== Trades


# TradesEntry = Tuple[Decimal, Decimal, Decimal, str, str, Optional[Any]]
TradesEntry = Tuple[Decimal, Decimal, Decimal, Literal["b", "s"], Literal["m", "l"], Optional[Any]]


class Trades(BaseModel):
    """ Trades Data Model

    Args:
        data (list) : array of <price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>
        last (Decimal) : id to be used as since when polling for new data
    """

    # data = List[Tuple[Decimal, Decimal, Decimal, Literal["b", "s"], Literal["m", "l"]]]
    # data = List[Tuple[Decimal, Decimal, Decimal, Any, Any, Optional[Any]]]
    data: List[TradesEntry]
    last: Decimal

    class Config:
        arbitrary_types_allowed = True




# ========================================
# ====== Spread


SpreadEntry = Tuple[Decimal, Decimal, Decimal]


class Spread(BaseModel):
    """Spread Data Model

    Args:
        data (list) : array of entries <time>, <bid>, <ask>
        last (Decimal) : id to be used as since when polling for new data
    """
    data: List[SpreadEntry]
    last: Decimal

    class Config:
        arbitrary_types_allowed = True




# ========================================
# ====== Account Balance


class AccountBalance(BaseModel):
    """Account Balance Data Model

    Args:
        data (dict) : format
            <asset> : <balance>
    """
    # tortoise ORM can not json serialize Decimal
    data: Dict[str, float]




# ========================================
# ====== Account Balance


class TradeBalanceData(TypedDict):
    equity_balance: float
    trade_balance: float
    positions_margin: float
    positions_unrealized: float
    positions_cost: float
    positions_valuation: float
    equity: float
    free_margin: float
    margin_level: float

class TradeBalance(BaseModel):
    """Trade Balance Data Model

    Args:
        data (dict) : keys
            equity_balance
            trade_balance
            positions_margin
            positions_unrealized
            positions_cost
            positions_valuation
            equity
            free_margin
            margin_level
    """
    # tortoise ORM can not json serialize Decimal
    data: TradeBalanceData




# ========================================
# ====== Orders


class Order(TypedDict):
    """
    Result: array of order info in open array with txid as the key

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
    status: Literal["pending", "open", "closed", "canceled", "expired"]
    opentm: Decimal
    starttm: Decimal
    expiretm: Decimal
    descr: dict
    vol: Decimal
    vol_exec: Decimal
    cost: Decimal
    fee: Decimal
    price: Optional[Decimal] = None
    stopprice: Optional[Decimal] = None
    limitprice: Optional[Decimal] = None
    misc: Optional[Any] = None
    oflags: Any
    trades: Any


class ClosedOrder(Order):

    closetm: Decimal
    reason: Optional[Any] = None


class OpenOrders(BaseModel):
    """Open Orders data model

    Args :

        data : dict of order info in open array with txid as the key

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
    # tortoise ORM can not json serialize Decimal
    data: Dict[str, Order]



class ClosedOrders(BaseModel):
    """
    Result: array of order info in open array with txid as the key

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
    """
    # tortoise ORM can not json serialize Decimal
    data: Dict[str, ClosedOrder]




# ========================================
# ==== Trades


class UserTradesEntry(TypedDict):
    """User Trades Data Model
    """
    ordertxid: str
    pair: str
    time: Decimal
    type: Literal["b", "s"]
    ordertype: Literal["m", "l"]
    price: Decimal
    cost: Decimal
    fee: Decimal
    vol: Decimal
    margin: Optional[Decimal] = None
    misc: Optional[Any] = None
    poststatus: Optional[Literal["open", "closed"]]
    cprice: Optional[Decimal]
    ccost: Optional[Decimal]
    cfee: Optional[Decimal]
    cvol: Optional[Decimal]
    cmargin: Optional[Decimal]
    net: Optional[Decimal]
    # list of what? not clear in doc
    trades: list



class UserTrades(BaseModel):
    """User Trades Data Model

    Args:
        data (dict): txid as key and tradeinfo dict as value
            tradeinfo :
            ordertxid = order responsible for execution of trade
            pair = asset pair
            time = unix timestamp of trade
            type = type of order (buy/sell)
            ordertype = order type
            price = average price order was executed at (quote currency)
            cost = total cost of order (quote currency)
            fee = total fee (quote currency)
            vol = volume (base currency)
            margin = initial margin (quote currency)
            misc = comma delimited list of miscellaneous info
                closing = trade closes all or part of a position

            If the trade opened a position, the follow fields are also present in the trade info:

            posstatus = position status (open/closed)
            cprice = average price of closed portion of position (quote currency)
            ccost = total cost of closed portion of position (quote currency)
            cfee = total fee of closed portion of position (quote currency)
            cvol = total fee of closed portion of position (quote currency)
            cmargin = total margin freed in closed portion of position (quote currency)
            net = net profit/loss of closed portion of position (quote currency, quote currency scale)
            trades = list of closing trades for position (if available)
    """
    data: Dict[str, UserTradesEntry]


# ========================================
# ==== Positions

class OpenPositionsEntry(TypedDict):
    ordertxid: str
    pair: str
    time: Decimal
    side: Literal["b", "s"]
    ordertype: Literal["l", "m"]
    cost: Decimal
    fee: Decimal
    vol: Decimal
    vol_closed: Decimal
    margin: Decimal
    value: Decimal
    net: Optional[Decimal] = None
    misc: Optional[Any] = None
    oflags: Optional[Any] = None


class OpenPositions(BaseModel):
    """Open Positions Data Model

    Args:
        data (dict):  position_txid as key and pos_info dict as value
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
    data: Dict[str, OpenPositionsEntry]




# ========================================
# ==== Placed Order


class PlacedOrder(BaseModel):
    """
    descr = order description info
        order = order description
        close = conditional close order description (if conditional close set)
    txid = array of transaction ids for order (if order was added successfully)
    """
