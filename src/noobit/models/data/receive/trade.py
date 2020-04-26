from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

from typing_extensions import Literal, TypedDict
from pydantic import BaseModel
from noobit.models.data.base_types import ORDERSTATUS, ORDERTYPE, ORDERSIDE




# ================================================================================
# ====== TRADES
# ================================================================================


class Trade(BaseModel):

    trade_id: Optional[str]

    side: ORDERSIDE
    type: ORDERTYPE

    pair: str
    timestamp: int

    price: Decimal
    volume: Decimal
    fee: Decimal
    slippage: Decimal = 0
    leverage: Decimal = 0