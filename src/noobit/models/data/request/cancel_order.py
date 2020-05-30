from typing import Optional, List

from pydantic import BaseModel



class CancelOrder(BaseModel):

    clOrdID: Optional[str]
    orderID: List[str]