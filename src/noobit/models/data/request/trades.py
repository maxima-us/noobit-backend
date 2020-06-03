from typing import Optional

from pydantic import BaseModel

from noobit.models.data.base.types import PAIR, TIMESTAMP


class TradesRequest(BaseModel):

    symbol: PAIR
    since: Optional[TIMESTAMP]