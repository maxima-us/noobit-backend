from typing import List, Any, Dict, Tuple, Optional
from decimal import Decimal

from typing_extensions import Literal, TypedDict
from pydantic import BaseModel



# ================================================================================
# ==== PRIVATE WS STATUS
# ================================================================================


class SubscriptionStatus(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-subscriptionStatus
    """

    channel_id: Optional[int] = None
    error_msg: Optional[str] = None
    channel_name: str
    event: str
    req_id: Optional[str] = None
    pair: Optional[str] = None
    status: str
    subscription: dict


class SystemStatus(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-systemStatus
    """
    connection_id: int
    event: str
    status: str
    version: str




# ================================================================================
# ==== PRIVATE WS HEARTBEAT
# ================================================================================


class HeartBeat(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-heartbeat
    """

    event: Literal["heartbeat"]



