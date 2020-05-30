from decimal import Decimal

from pydantic import BaseModel

from noobit.models.data.base.types import PAIR, TIMESTAMP



class Spread(BaseModel):

    symbol: PAIR
    bestBid: Decimal
    bestAsk: Decimal
    utcTime: TIMESTAMP