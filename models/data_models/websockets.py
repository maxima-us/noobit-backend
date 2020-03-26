from typing import List, Any, Dict, Tuple, Optional, Union
from typing_extensions import Literal, TypedDict
from enum import Enum
from decimal import Decimal

from pydantic import BaseModel

from models.data_models.api import TickerItem


# ================================================================================
# ================================================================================
# ==== PRIVATE WS STATUS


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
# ==== PRIVATE WS HEARTBEAT


class HeartBeat(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-heartbeat
    """
    
    event: Literal["heartbeat"]




# ================================================================================
# ================================================================================
# ==== PRIVATE WS DATA


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

    data : Dict[str, OpenOrdersItem]
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

    data : Dict[str, OwnTradesItem]
    channel_name : str






# ================================================================================
# ================================================================================
# ==== PUBLIC WS DATA


class TickerEntry(TypedDict):
    """
    a: <price>, <wholeLotVolume>, <lotVolume>
    b: <price>, <wholeLotVolume>, <lotVolume>
    c: <price>, <lotVolume>
    v: <today>, <last24Hours>
    p: <today>, <last24Hours> 
    t: <today>, <last24Hours> 
    l: <today>, <last24Hours> 
    h: <today>, <last24Hours> 
    o: <today>, <last24Hours> 
    """
    a: Tuple[Decimal, int, Decimal]
    b: Tuple[Decimal, int, Decimal]
    c: Tuple[Decimal, Decimal]
    v: Tuple[Decimal, Decimal]
    p: Tuple[Decimal, Decimal]
    t: Tuple[Decimal, Decimal]
    l: Tuple[Decimal, Decimal]
    h: Tuple[Decimal, Decimal]
    o: Tuple[Decimal, Decimal]




class Ticker(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-ticker
    """
    channel_id : int
    data : TickerEntry
    channel_name : str 
    pair : str




# array of <price>, <volume>, <time>, <side>, <orderType>, <misc>
TradeEntry = Tuple[Decimal, Decimal, Decimal, str, str, str]


class Trade(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-trade
    """
    channel_id : int
    data : List[TradeEntry]
    channel_name : str
    pair : str





# array of <bid>, <ask>, <timestamp>, <bidVolume>, <askVolume>
SpreadEntry = Tuple[Decimal, Decimal, Decimal, Decimal, Decimal]

class Spread(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-spread 
    """
    channel_id: int
    data: SpreadEntry
    channel_name: str
    pair: str





class BookSnapshot(TypedDict):
    """
    as: ask array of <price>, <volume>, <timestamp>
    bs: bids array of <price>, <volume>, <timestamp>

    we have to set keys to <asks> and <bids> because as is reserved in py
    """
    asks: List[Tuple[Decimal, Decimal, Decimal]]
    bids: List[Tuple[Decimal, Decimal, Decimal]]


class BookEntry(TypedDict):
    """
    a: array of <price>, <volume>, <timestamp>, <updateType>
    b: array of <price>, <volume>, <timestamp>, <updateType>
    
    Notes :
        updateType:
            Optional - "r" in case update is a republished update
    """
    a: List[Tuple[Decimal, Decimal, Decimal, Optional[str]]]
    b: List[Tuple[Decimal, Decimal, Decimal, Optional[str]]]


class Book(BaseModel):
    """
    kraken : https://docs.kraken.com/websockets/#message-book
    """
    channel_id: int
    data: BookEntry
    channel_name: str 
    pair: str