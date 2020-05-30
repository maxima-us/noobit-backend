from typing import Optional
from decimal import Decimal

from typing_extensions import Literal
from pydantic import BaseModel, Field

from noobit.models.data.base.types import ORDERSIDE, ORDERTYPE, PAIR, PERCENT, TIMESTAMP


class AddOrder(BaseModel):

    symbol: PAIR
    side: ORDERSIDE
    ordType: ORDERTYPE
    execInst: Optional[str]
    clOrdID: Optional[str] = Field(...)
    timeInForce: Optional[str] = Field(...)
    effectiveTime: Optional[TIMESTAMP]
    expireTime: Optional[TIMESTAMP]
    orderQty: Decimal
    orderPercent: Optional[PERCENT]
    # cashMargin: Literal["cash", "margin"]         # do we need this ?
    marginRatio: Decimal
    price: Decimal
    stopPx: Decimal
    targetStrategy: Optional[str]
    targetStrategyParameters: Optional[dict]
