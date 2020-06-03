from pydantic import BaseModel

from  noobit.models.data.base.types import PAIR 

class InstrumentRequest(BaseModel):
    symbol: PAIR