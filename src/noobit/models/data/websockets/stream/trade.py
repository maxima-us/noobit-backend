from typing import List
from typing_extensions import Literal

from pydantic import BaseModel

from noobit.models.data.response.trade import (
    Trade as TradeRestModel,
)


# for now we just use the same model, maybe later we will change ?
# seems to be easier to have the same models across the app
class Trade(TradeRestModel):

    exchange: str

    # As defined in bitmex ws api: https://www.bitmex.com/app/wsAPI
    #   The type of the message. Types:
    #   'partial'; This is a table image, replace your data entirely.
    #   'update': Update a single row.
    #   'insert': Insert a new row.
    #   'delete': Delete a row.
    #   "action": 'partial' | 'update' | 'insert' | 'delete',
    action: Literal["partial", "update", "insert", "delete"] = "insert"


class TradesList(BaseModel):

    channel = "trade"
    data: List[Trade]