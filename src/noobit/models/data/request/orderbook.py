from pydantic import BaseModel

from noobit.models.data.base.types import PAIR

class OrderBookRequest(BaseModel):

    symbol: PAIR