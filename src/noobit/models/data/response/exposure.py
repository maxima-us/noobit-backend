from decimal import Decimal
from typing import Optional
from datetime import datetime

from pydantic import BaseModel

from noobit.models.data.base.types import TIMESTAMP



class Exposure(BaseModel):

    # CCXT equivalence: timestamp
    # FIX Definition: https://fixwiki.org/fixwiki/SendingTime
    #   Time of message transmission
    #   always expressed in UTC (Universal Time Coordinated, also known as "GMT")
    #! useless + creates problem when wanting to serialize
    #!  (datetime not serializable)
    # sendingTime: TIMESTAMP = datetime.utcnow()

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.4/tagNum_900.html
    # (Total value of assets + positions + unrealized)
    totalNetValue: Decimal

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.4/tagNum_901.html
    # (Available cash after deducting margin)
    cashOutstanding: Optional[Decimal]

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.4/tagNum_899.html
    #   Excess margin amount (deficit if value is negative)
    # (Available margin)
    marginExcess: Decimal

    # FIX Definition:
    #   The fraction of the cash consideration that must be collateralized, expressed as a percent.
    #   A MarginRatio of 02% indicates that the value of the collateral (after deducting for "haircut")
    #   must exceed the cash consideration by 2%.
    # (marginRatio = 1/leverage)
    # (total margin exposure on account)
    marginRatio: Decimal = 0

    marginAmt: Decimal = 0

    unrealisedPnL: Decimal = 0