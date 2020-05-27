from typing import Dict, List, Optional
from decimal import Decimal

from typing_extensions import Literal
from pydantic import BaseModel
from noobit.models.data.base.types import ORDERSTATUS, ORDERTYPE, ORDERSIDE




# ================================================================================
# ====== ORDERS
# ================================================================================


class Order(BaseModel):

    order_id: Optional[str] = None
    pair: str

    status: ORDERSTATUS
    type: ORDERTYPE
    side: ORDERSIDE

    time_open: int
    time_start: int
    time_expire: int

    volume_total: Decimal
    volume_filled: Decimal = 0

    cost: Decimal
    fee: Decimal

    # can be None if we place a market order
    # info[descr][price]
    price_limit: Optional[Decimal] = None
    price_tp: Optional[Decimal] = None
    price_sl: Optional[Decimal] = None
    #info[price]
    price_avg_fill: Optional[Decimal] = None

    leverage: Optional[int] = None

    trades: Optional[List[str]] = None


class ClosedOrder(Order):

    close_time: int
    reason: Optional[str]


class OpenOrders(BaseModel):
    data: Dict[str, Order]


class ClosedOrders(BaseModel):
    data: Dict[str, ClosedOrder]