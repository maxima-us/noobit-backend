from typing import List, Any, Dict, Tuple, Optional
from decimal import Decimal

from typing_extensions import Literal, TypedDict
from pydantic import BaseModel


# ================================================================================
# ==== USER TRADING
# ================================================================================


class AddOrder(BaseModel):
    """
    kraken: https://docs.kraken.com/websockets/#message-addOrder
    """
    event: Literal["addOrder"]
    token: str
    reqid: Optional[int] = 1
    ordertype: str
    type: str
    pair: str
    price: Optional[str] = ''
    price2: Optional[str] = ''
    volume: str
    leverage: Optional[str] = ''
    # oflags: Optional[List[str]]
    starttm: Optional[str] = ''
    expiretm: Optional[str] = ''
    userref: Optional[str] = ''


class CancelOrder(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-cancelOrder
    """
    event: Literal["cancelOrder"]
    token: str
    reqid: Optional[int] = 1
    txid: List[str]
