from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from typing_extensions import Literal, TypedDict
from pydantic import BaseModel



from noobit.models.data.base.types import ORDERSTATUS, ORDERTYPE, ORDERSIDE, PERCENT, PAIR, TIMESTAMP



class Order(BaseModel):

    # FIX Definition:
    #   Unique identifier for Order as assigned by sell-side (broker, exchange, ECN).
    #   Uniqueness must be guaranteed within a single trading day.
    #   Firms which accept multi-day orders should consider embedding a date
    #   within the OrderID field to assure uniqueness across days.
    orderID: str

    # FIX Definition:
    #   Unique identifier for Order as assigned by the buy-side (institution, broker, intermediary etc.)
    #   (identified by SenderCompID (49) or OnBehalfOfCompID (5) as appropriate).
    #   Uniqueness must be guaranteed within a single trading day.
    #   Firms, particularly those which electronically submit multi-day orders, trade globally
    #   or throughout market close periods, should ensure uniqueness across days, for example
    #   by embedding a date within the ClOrdID field.
    clOrdID: str

    # FIX Definition:
    #   Account mnemonic as agreed between buy and sell sides, e.g. broker and institution
    #   or investor/intermediary and fund manager.
    account: str

    # FIX Definition:
    #   Ticker symbol. Common, "human understood" representation of the security.
    #   SecurityID (48) value can be specified if no symbol exists
    #   (e.g. non-exchange traded Collective Investment Vehicles)
    #   Use "[N/A]" for products which do not have a symbol.
    symbol: PAIR

    # FIX Definition:
    #   Identifies currency used for price.
    #   Absence of this field is interpreted as the default for the security.
    #   It is recommended that systems provide the currency value whenever possible.
    currency: str

    # FIX Definition: https://fixwiki.org/fixwiki/Side
    #   Side of order
    side: ORDERSIDE

    # CCXT equivalence: type
    # FIX Definition: https://fixwiki.org/fixwiki/OrdType
    #   Order type
    ordType: ORDERTYPE

    # FIX Definition: https://fixwiki.org/fixwiki/CashMargin
    #   Identifies whether an order is a margin order or a non-margin order.
    cashMargin: str

    # CCXT equivalence: status
    # FIX Definition: https://fixwiki.org/fixwiki/OrdStatus
    #   Identifies current status of order.
    ordStatus: ORDERSTATUS

    # FIX Definition: https://fixwiki.org/fixwiki/WorkingIndicator
    #   Indicates if the order is currently being worked.
    #   Applicable only for OrdStatus = "New".
    #   For open outcry markets this indicates that the order is being worked in the crowd.
    #   For electronic markets it indicates that the order has transitioned from a contingent order
    #       to a market order.
    workingIndicator: bool

    # FIX Definition: https://fixwiki.org/fixwiki/OrdRejReason
    #   Code to identify reason for order rejection.
    #   Note: Values 3, 4, and 5 will be used when rejecting an order due to
    #   pre-allocation information errors.
    ordRejReason: str


    # ================================================================================


    # FIX Definition: https://fixwiki.org/fixwiki/TimeInForce
    #   Specifies how long the order remains in effect.
    #   Absence of this field is interpreted as DAY.
    timeInForce: str

    # CCXT equivalence: lastTradeTimestamp
    # FIX Definition: https://fixwiki.org/fixwiki/TransactTime
    #   Timestamp when the business transaction represented by the message occurred.
    transactTime: TIMESTAMP

    # CCXT equivalence: timestamp
    # FIX Definition: https://fixwiki.org/fixwiki/SendingTime
    #   Time of message transmission (
    #   always expressed in UTC (Universal Time Coordinated, also known as "GMT")
    sendingTime: TIMESTAMP

    # FIX Definition: https://fixwiki.org/fixwiki/EffectiveTime
    #   Time the details within the message should take effect
    #   (always expressed in UTC)
    effectiveTime: TIMESTAMP

    # FIX Definition: https://fixwiki.org/fixwiki/ValidUntilTime
    #   Indicates expiration time of indication message
    #   (always expressed in UTC)
    validUntilTime: TIMESTAMP

    # FIX Definition: https://fixwiki.org/fixwiki/ExpireTime
    #   Time/Date of order expiration
    #   (always expressed in UTC)
    expireTime: TIMESTAMP


    # ================================================================================
    # The OrderQtyData component block contains the fields commonly used
    # for indicating the amount or quantity of an order.
    # Note that when this component block is marked as "required" in a message
    # either one of these three fields must be used to identify the amount:
    # OrderQty, CashOrderQty or OrderPercent (in the case of CIV).
    # ================================================================================

    # Optional quantity to display in the book.
    # Use 0 for a fully hidden order.
    displayQty: Decimal

    grossTradeAmt: Decimal

    # CCXT equivalence: amount
    # FIX Definition: https://fixwiki.org/fixwiki/OrderQty
    #   Quantity ordered. This represents the number of shares for equities
    #   or par, face or nominal value for FI instruments.
    orderQty: Decimal

    # FIX Definition: https://fixwiki.org/fixwiki/CashOrderQty
    #   Specifies the approximate order quantity desired in total monetary units
    #   vs. as tradeable units (e.g. number of shares).
    cashOrderQty: Decimal

    # FIX Definition: https://fixwiki.org/fixwiki/OrderPercent
    #   For CIV specifies the approximate order quantity desired.
    #   For a CIV Sale it specifies percentage of investor's total holding to be sold.
    #   For a CIV switch/exchange it specifies percentage of investor's cash realised
    #       from sales to be re-invested.
    #   The executing broker, intermediary or fund manager is responsible for converting
    #       and calculating OrderQty (38) in shares/units for subsequent messages.
    orderPercent: PERCENT

    # CCXT equivalence: filled
    # FIX Definition: https://fixwiki.org/fixwiki/CumQty
    #   Total quantity (e.g. number of shares) filled.
    cumQty: Decimal

    # CCXT equivalence: remaining
    # FIX Definition: https://fixwiki.org/fixwiki/LeavesQty
    #   Quantity open for further execution.
    #   If the OrdStatus (39) is Canceled, DoneForTheDay, Expired, Calculated, or Rejected
    #   (in which case the order is no longer active) then LeavesQty could be 0,
    #   otherwise LeavesQty = OrderQty (38) - CumQty (14).
    leavesQty: Decimal


    # ================================================================================


    # FIX Definition: https://fixwiki.org/fixwiki/Price
    #   Price per unit of quantity (e.g. per share)
    price: Decimal

    # FIX Definition:
    #   Price per unit of quantity (e.g. per share)
    stopPx: Decimal

    # FIX Definition: https://fixwiki.org/fixwiki/AvgPx
    #   Calculated average price of all fills on this order.
    avgPX: Decimal


    # ================================================================================


    # CCXT equivalence: fee
    # FIX Definition: https://fixwiki.org/fixwiki/Commission
    #   Commission
    commission: Decimal


    # ================================================================================


    # FIX Definition: https://fixwiki.org/fixwiki/TargetStrategy
    #   The target strategy of the order
    targetStrategy: str

    # FIX Definition: https://fixwiki.org/fixwiki/TargetStrategyParameters
    #   Field to allow further specification of the TargetStrategy
    #   Usage to be agreed between counterparties
    targetStrategyParameters: Dict


# {
#     "orderID": "string",
#     "clOrdID": "string",
#     "clOrdLinkID": "string",
#     "account": 0,
#     "symbol": "string",
#     "side": "string",
#     "simpleOrderQty": 0,
#     "orderQty": 0,
#     "price": 0,
#     "displayQty": 0,
#     "stopPx": 0,
#     "pegOffsetValue": 0,
#     "pegPriceType": "string",
#     "currency": "string",
#     "settlCurrency": "string",
#     "ordType": "string",
#     "timeInForce": "string",
#     "execInst": "string",
#     "contingencyType": "string",
#     "exDestination": "string",
#     "ordStatus": "string",
#     "triggered": "string",
#     "workingIndicator": true,
#     "ordRejReason": "string",
#     "simpleLeavesQty": 0,
#     "leavesQty": 0,
#     "simpleCumQty": 0,
#     "cumQty": 0,
#     "avgPx": 0,
#     "multiLegReportingType": "string",
#     "text": "string",
#     "transactTime": "2020-04-24T15:22:43.111Z",
#     "timestamp": "2020-04-24T15:22:43.111Z"
#   }