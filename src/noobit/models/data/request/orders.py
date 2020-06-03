from typing import Optional, Union

from typing_extensions import Literal
from pydantic import BaseModel, Field

from noobit.models.data.base.types import PAIR

class OrdersRequest(BaseModel):
    mode: Literal["to_list", "by_id"]

    # kraken is str but other exchanges may be int
    orderID: Optional[Union[str, int]] = Field(...)
    symbol: Optional[PAIR] = Field(...)
    clOrderID: Optional[int] = Field(...)
