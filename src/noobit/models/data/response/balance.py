from typing import Dict, Optional, List
from decimal import Decimal

from typing_extensions import Literal
from pydantic import BaseModel

from noobit.models.data.base.types import PAIR, TIMESTAMP


# Instrument Component: https://www.onixs.biz/fix-dictionary/4.4/compBlock_Instrument.html
# Position Qty Component: https://www.onixs.biz/fix-dictionary/4.4/compBlock_PositionQty.html

#! Not entirely sure yet how to handle balances and positions


class Position(BaseModel):

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.4/tagNum_55.html
    #   Ticker symbol. Common, "human understood" representation of the security
    symbol: PAIR

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.4/tagNum_704.html
    #   Long Quantity
    longQty: Decimal = 0

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.4/tagNum_705.html
    #   Short Quantity
    shortQty: Decimal = 0

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.4/tagNum_708.html
    #   Position Amount
    posAmt: Decimal = 0

    # FIX Definition: https://fixwiki.org/fixwiki/CashMargin
    #   Identifies whether an order is a margin order or a non-margin order.
    #   One of: [Cash, MarginOpen, MarginClose]
    # We simplify it to just [cash, margin]
    cashMargin: Literal["cash", "margin"]

    # FIX Definition:
    #   The fraction of the cash consideration that must be collateralized, expressed as a percent.
    #   A MarginRatio of 02% indicates that the value of the collateral (after deducting for "haircut")
    #   must exceed the cash consideration by 2%.
    # (marginRatio = 1/leverage)
    marginRatio: Decimal = 0



class Balance(BaseModel):

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.2/tagNum_15.html
    currency: str

    # CCXT equivalence: filled
    # FIX Definition: https://fixwiki.org/fixwiki/CumQty
    #   Total quantity (e.g. number of shares) filled.
    cumQty: Decimal = 0



class Balances(BaseModel):

    # CCXT equivalence: timestamp
    # FIX Definition: https://fixwiki.org/fixwiki/SendingTime
    #   Time of message transmission
    #   always expressed in UTC (Universal Time Coordinated, also known as "GMT")
    sendingTime: Optional[TIMESTAMP]

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.4/tagNum_900.html
    # (Total value of assets + positions + unrealized)
    totalNetvalue: Decimal

    # FIX Definition: https://www.onixs.biz/fix-dictionary/4.4/tagNum_901.html
    # (Available cash after deducting margin)
    cashOutstanding: Decimal

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


    # ================================================================================


    balances: List[Balance]

