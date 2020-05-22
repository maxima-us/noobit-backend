from typing import Tuple, List, Dict, Optional, Counter
from decimal import Decimal
from datetime import datetime

from typing_extensions import Literal
from pydantic import BaseModel, conint, constr




# ================================================================================
# ====== ORDERS
# ================================================================================


# KRAKEN: Other advanced order types such as stop-loss-limit are not enabled
ORDERTYPE = Literal[
    # kraken
    "market",
    "limit",
    "stop-loss",
    "take-profit",
    "settle-position",

    # binance
    "stop-loss-limit",
    "take-profit-limit",
    "limit-maker"
]


ORDERSIDE = Literal[
    "buy",
    "sell",
]


# See https://fixwiki.org/fixwiki/OrdStatus
ORDERSTATUS = Literal[
    "pending-new",
    "new",
    "partially-filled",
    "filled",
    "pending-cancel",
    "canceled",
    "closed",
    "expired",
    "rejected"
    ""
]


TIMEINFORCE = Literal[
    "good-till-cancel",
    "immediate-or-cancel",
    "fill-or-kill",
]




# ================================================================================
# ====== GENERAL
# ================================================================================


PERCENT = conint(ge=0, le=100, multiple_of=1)

PAIR = constr(regex=r'[A-Z]+-[A-Z]+')

# datetime can not be efficiently serialized to json
# has to be int so we make sure timestamp in in nanoseconds
# example: 1589083212696600000
# and not: 1589083212.6966 (what we would receive from kraken)
TIMESTAMP = int




# ================================================================================
# ====== ORDERBOOKS
# ================================================================================


# dict of { <price> : <volume> }
ASK = Dict[Decimal, Decimal]
# ASKS = Counter[Decimal]
ASKS = Dict[Decimal, Decimal]

BID = Dict[Decimal, Decimal]
# BIDS = Counter[Decimal]
BIDS = Dict[Decimal, Decimal]



# ================================================================================
# ====== SPREAD
# ================================================================================


# tuple of <best bid>, <best ask>, <timestamp>
SPREAD = Tuple[Decimal, Decimal, Decimal]




# ================================================================================
# ====== FILLS
# ================================================================================

# FIX Fills Group: https://www.onixs.biz/fix-dictionary/5.0.sp2/compBlock_FillsGrp.html
class Fill(BaseModel):

    # FIX Definition:
    #   Unique identifier of execution as assigned by sell-side (broker, exchange, ECN).
    #   Must not overlap ExecID(17). Required if NoFills > 0
    fillExecID: str

    # FIX Definition:
    #   Price of this partial fill.
    #   Conditionally required if NoFills > 0.
    fillPx: Optional[Decimal]

    # FIX Definition:
    #   Quantity (e.g. shares) bought/sold on this partial fill.
    #   Required if NoFills > 0.
    fillQty: Optional[Decimal]

    # FIX Definition:
    #   Specifies the number of partial fills included in this Execution Report
    noFills: int


FILLS = List[Fill]




# ================================================================================
# ====== OHLC
# ================================================================================


TIMEFRAME = Literal[
    1,
    5,
    15,
    30,
    60,
    240,
    1440,
    10080,
    21600
]

INTERVAL = Literal[
    "second",
    "minute",
    "hour",
    "day",
    "week"
]


# tuple of <timestamp>, <open>, <high>, <low>, <close>, <volume>
OHLC = Tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]


# ================================================================================
# ====== TRANSACTIONS
# ================================================================================


TRANSACTIONTYPE = Literal[
    "withdrawal",
    "deposit",
]



# ================================================================================
# ====== TRANSACTIONS
# ================================================================================

WS_ROUTE = [
    "heartbeat",
    "system_status",
    "subscription_status",

    "trade",
    "instrument",
    "orderbook",
    "spread",
    "order",

    "data"
]