from typing import Dict, Optional, List
from decimal import Decimal

from typing_extensions import Literal
from pydantic import BaseModel



from noobit.models.data.base.types import ORDERSTATUS, ORDERTYPE, ORDERSIDE, PERCENT, PAIR, TIMESTAMP, FILLS


# FIX Trade Capture Report: https://www.onixs.biz/fix-dictionary/4.4/msgtype_ae_6569.html
#! should be add session ID ? to identify a particular trading session ??
#! see: https://www.onixs.biz/fix-dictionary/4.4/tagNum_336.html


class Trade(BaseModel):


    # FIX Definition: https://fixwiki.org/fixwiki/TrdMatchID
    #   Identifier assigned to a trade by a matching system.
    trdMatchID: Optional[str]

    # FIX Definition:
    #   Unique identifier for Order as assigned by sell-side (broker, exchange, ECN).
    #   Uniqueness must be guaranteed within a single trading day.
    #   Firms which accept multi-day orders should consider embedding a date
    #   within the OrderID field to assure uniqueness across days.
    orderID: Optional[str]

    # FIX Definition:
    #   Unique identifier for Order as assigned by the buy-side (institution, broker, intermediary etc.)
    #   (identified by SenderCompID (49) or OnBehalfOfCompID (5) as appropriate).
    #   Uniqueness must be guaranteed within a single trading day.
    #   Firms, particularly those which electronically submit multi-day orders, trade globally
    #   or throughout market close periods, should ensure uniqueness across days, for example
    #   by embedding a date within the ClOrdID field.
    clOrdID: Optional[str]

    # FIX Definition:
    #   Ticker symbol. Common, "human understood" representation of the security.
    #   SecurityID (48) value can be specified if no symbol exists
    #   (e.g. non-exchange traded Collective Investment Vehicles)
    #   Use "[N/A]" for products which do not have a symbol.
    symbol: PAIR

    # FIX Definition: https://fixwiki.org/fixwiki/Side
    #   Side of order
    side: ORDERSIDE

    # CCXT equivalence: type
    # FIX Definition: https://fixwiki.org/fixwiki/OrdType
    #   Order type
    ordType: ORDERTYPE

    # FIX Definition: https://fixwiki.org/fixwiki/AvgPx
    #   Calculated average price of all fills on this order.
    avgPx: Decimal

    # CCXT equivalence: filled
    # FIX Definition: https://fixwiki.org/fixwiki/CumQty
    #   Total quantity (e.g. number of shares) filled.
    cumQty: Decimal

    # CCXT equivalence: cost
    # FIX Definition: https://fixwiki.org/fixwiki/GrossTradeAmt
    #   Total amount traded (i.e. quantity * price) expressed in units of currency.
    #   For Futures this is used to express the notional value of a fill when quantity fields are expressed in terms of contract size
    grossTradeAmt: Decimal

    # CCXT equivalence: fee
    # FIX Definition: https://fixwiki.org/fixwiki/Commission
    #   Commission
    commission: Optional[Decimal]

    # CCXT equivalence: lastTradeTimestamp
    # FIX Definition: https://fixwiki.org/fixwiki/TransactTime
    #   Timestamp when the business transaction represented by the message occurred.
    transactTime: Optional[TIMESTAMP]

    # FIX Definition: https://fixwiki.org/fixwiki/TickDirection
    #   Direction of the "tick"
    tickDirection: Optional[Literal["PlusTick", "ZeroPlusTick", "MinusTick", "ZeroMinusTick"]]

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.4/tagNum_58.html
    #   Free format text string
    #   May be used by the executing market to record any execution Details that are particular to that market
    # Use to store misc info
    text: Optional[str]


# ================================================================================


class TradesList(BaseModel):
    data: List[Trade]


class TradesByID(BaseModel):
    data: Dict[str, Trade]


# ================================================================================


# KRAKEN DOC
# trades = array of trade info with txid as the key
#     ordertxid = order responsible for execution of trade
#     pair = asset pair
#     time = unix timestamp of trade
#     type = type of order (buy/sell)
#     ordertype = order type
#     price = average price order was executed at (quote currency)
#     cost = total cost of order (quote currency)
#     fee = total fee (quote currency)
#     vol = volume (base currency)
#     margin = initial margin (quote currency)
#     misc = comma delimited list of miscellaneous info
#         closing = trade closes all or part of a position
# count = amount of available trades info matching criteria

# EXAMPLE OF KRAKEN RESPONSE
# {
#   "TZ63HS-YBD4M-3RDG7H": {
#     "ordertxid": "OXXRD7-L67OU-QWHJEZ",
#     "postxid": "TKH1SE-M7IF3-CFI4LT",
#     "pair": "ETH-USD",
#     "time": 1588032030.4648,
#     "type": "buy",
#     "ordertype": "market",
#     "price": "196.94000",
#     "cost": "7395.50936",
#     "fee": "14.79101",
#     "vol": "37.55209384",
#     "margin": "0.00000",
#     "misc": ""
#   },
#   "TESD4J-6G7RU-K5C9TU": {
#     "ordertxid": "ORZGFF-GENRB-Z20HTV",
#     "postxid": "T6HT2W-ER1S7-5MVQGW",
#     "pair": "ETH-USD",
#     "time": 1588032024.6599,
#     "type": "buy",
#     "ordertype": "market",
#     "price": "196.93124",
#     "cost": "6788.34719",
#     "fee": "13.57670",
#     "vol": "34.47064696",
#     "margin": "1697.08680",
#     "misc": "closing"
#   },
#   "TEF2TE-RRBVG-FLFHG6": {
#     "ordertxid": "OL1AHL-OOF5D-V3KKJM",
#     "postxid": "TKH0SE-M1IF3-CFI1LT",
#     "posstatus": "closed",
#     "pair": "ETH-USD",
#     "time": 1585353611.261,
#     "type": "sell",
#     "ordertype": "market",
#     "price": "131.01581",
#     "cost": "7401.30239",
#     "fee": "17.76313",
#     "vol": "56.49167433",
#     "margin": "1850.32560",
#     "misc": ""
#   }
# }


# EXAMPLE OF BITMEX RESPONSE
# [
#   {
#     "timestamp": "2020-05-01T10:02:59.169Z",
#     "symbol": "string",
#     "side": "string",
#     "size": 0,
#     "price": 0,
#     "tickDirection": "string",
#     "trdMatchID": "string",
#     "grossValue": 0,
#     "homeNotional": 0,
#     "foreignNotional": 0
#   }
# ]
# [
#  {
#  "timestamp": "2018-12-14T17:04:27.127Z",     // When the trade happened according to bitmex server timestamp
#  "symbol": "XBTUSD",                          // which contract is this
#  "side": "Sell",                              // The taker side
#  "size": 5,                                   // How many contracts; just for convenience you can think of these as USD
#  "price": 3170.5,                             // pride of the contract
#  "tickDirection": "MinusTick",                // This trade happened at a price lower than the previous one
#  "trdMatchID": "15cdac8e-ccdc-5d4b-1300-a0899574239d", // ID of this trade. It should always be unique.
#  "grossValue": 157705,                        // How many sathoshi were exchanged == 5/3170.5*100000000
#  "homeNotional": 0.00157705,                  // How many BTC was this trade worth
#  "foreignNotional": 5                         // How many USD was this trade worth
#  }
#]