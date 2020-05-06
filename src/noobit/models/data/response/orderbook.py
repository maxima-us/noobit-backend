from pydantic import BaseModel

from noobit.models.data.base.types import ASKS, BIDS, TIMESTAMP


class OrderBook(BaseModel):

    utcTime: TIMESTAMP
    asks: ASKS
    bids: BIDS