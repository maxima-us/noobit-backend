from decimal import Decimal
from typing import List
from typing_extensions import Literal

from pydantic import BaseModel

from noobit.models.data.base.types import PAIR
from noobit.models.data.response.ohlc import (
    OhlcItem as OhlcRestItem
)


class OhlcItem(BaseModel):
    symbol: PAIR
    utcTime: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trdCount: Decimal


class Ohlc(OhlcRestItem):
    channel: str = "ohlc"
    exchange: str
    action: Literal["partial", "update", "insert", "delete"] = "insert"
    data: List[OhlcItem]