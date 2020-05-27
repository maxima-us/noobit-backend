from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from noobit.models.data.base.types import ASK, BID, TIMESTAMP, PAIR


class Instrument(BaseModel):


    # FIX Definition:
    #   Ticker symbol. Common, "human understood" representation of the security.
    #   SecurityID (48) value can be specified if no symbol exists
    #   (e.g. non-exchange traded Collective Investment Vehicles)
    #   Use "[N/A]" for products which do not have a symbol.
    symbol: PAIR

    # prices
    low: Decimal
    high: Decimal
    vwap: Decimal
    last: Decimal
    # specific to derivatives exchanges
    markPrice: Optional[Decimal]

    # quantities
    volume: Decimal
    trdCount: Decimal

    # spread
    bestAsk: ASK
    bestBid: BID

    # stats for previous day
    prevLow: Decimal
    prevHigh: Decimal
    prevVwap: Decimal
    prevVolume: Decimal
    prevTrdCount: Optional[Decimal]
