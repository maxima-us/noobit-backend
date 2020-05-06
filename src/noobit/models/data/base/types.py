from typing import Tuple, List
from decimal import Decimal
from datetime import datetime

from typing_extensions import Literal, TypedDict
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

TIMESTAMP = datetime




# ================================================================================
# ====== ORDERBOOKS
# ================================================================================


# tuple of <price>, <volume>
ASK = Tuple[Decimal, Decimal]
ASKS = List[ASK]

BID = Tuple[Decimal, Decimal]
BIDS = List[BID]



# ================================================================================
# ====== SPREAD
# ================================================================================


# tuple of <best bid>, <best ask>, <timestamp>
SPREAD = Tuple[Decimal, Decimal, Decimal]




# ================================================================================
# ====== FILLS
# ================================================================================

class Fill(TypedDict):
    fillExecID: str
    fillPx: Decimal
    fillQty: Decimal
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