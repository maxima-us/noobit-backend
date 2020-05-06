from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel


class OhlcItem(BaseModel):

    utcTime: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trdCount: Decimal


class Ohlc(BaseModel):

    data: List[OhlcItem]