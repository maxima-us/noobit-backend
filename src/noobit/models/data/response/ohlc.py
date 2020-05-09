from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel

from noobit.models.data.base.types import PAIR


class OhlcItem(BaseModel):

    symbol: PAIR
    utcTime: datetime

    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    trdCount: Decimal


class Ohlc(BaseModel):

    data: List[OhlcItem]