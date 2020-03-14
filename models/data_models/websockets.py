from typing import List, Any, Dict, Tuple, Optional, Union
from typing_extensions import Literal, TypedDict
from datetime import date
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel

from models.data_models.api import TickerItem


# ================================================================================
# ================================================================================
# ==== STATUS


class SubscriptionStatus(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-subscriptionStatus
    """

    channel_id : Optional[int]=None
    error_msg : Optional[str]=None
    channel_name : str
    event : str
    req_id : Optional[str]=None
    pair : Optional[str]=None
    status : str
    subscription : dict


class SystemStatus(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-systemStatus
    """
    connection_id : int
    event : str
    status : str
    version : str




# ================================================================================
# ================================================================================
# ==== HEARTBEAT


class HeartBeat(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-heartbeat
    """
    
    event: Literal["heartbeat"]




# ================================================================================
# ================================================================================
# ==== DATA


class OpenOrdersItem(TypedDict):
    """
    kraken : https://docs.kraken.com/websockets/#message-openOrders
    """

    refid : str
    userref : str
    status : str
    opentm : str
    starttm : str=None
    expiretm : str=None
    descr : dict
    vol : Decimal
    vol_exec : Decimal
    cost : Decimal
    fee : Decimal 
    avg_price : Decimal
    stopprice : Decimal
    limitprice : Decimal
    misc : Any
    oflags : Optional[Any]




class OpenOrders(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-openOrders
    """

    data : List[Dict[str, OpenOrdersItem]]
    channel_name : str



class OwnTradesItem(TypedDict):
    """
    kraken : https://docs.kraken.com/websockets/#message-ownTrades
    """

    ordertxid : str
    posttxid : str
    pair : str
    time : Decimal
    type : str
    ordertype : str
    cost : Decimal
    fee : Decimal
    vol : Decimal
    margin : Decimal


class OwnTrades(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-ownTrades
    """

    data : List[Dict[str, OwnTradesItem]]
    channel_name : str






