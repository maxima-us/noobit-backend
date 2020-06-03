from pydantic import BaseModel

from noobit.models.data.base.types import PAIR, TIMEFRAME


class OhlcRequest(BaseModel):

    symbol: PAIR
    timeframe: TIMEFRAME