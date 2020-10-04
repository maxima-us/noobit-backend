from typing import Optional
from typing_extensions import Literal
from pydantic import BaseModel, PositiveInt, validator

from noobit.models.data.base.types import WS, PAIR


class ConnectionStatus(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-systemStatus
    """

    exchange: str
    connection_id: PositiveInt
    status: Literal["online", "offline"]
    version: str


class SubscriptionStatus(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-subscriptionStatus
    """

    exchange: str
    feed: WS
    symbol: PAIR
    status: Literal["subscribed", "unsubscribed", "error"]
    args: dict
    msg: str


class HeartBeat(BaseModel):

    exchange: str
