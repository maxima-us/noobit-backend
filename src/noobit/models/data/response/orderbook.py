from datetime import datetime

from pydantic import BaseModel

from noobit.models.data.base.types import ASKS, BIDS, TIMESTAMP, PAIR


class OrderBook(BaseModel):

    sendingTime: TIMESTAMP = datetime.utcnow()
    symbol: PAIR
    asks: ASKS
    bids: BIDS