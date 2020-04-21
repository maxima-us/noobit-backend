import uuid
import time
from tortoise import fields, models

from .orders import Order
from .exchange import Exchange

#!  on startup we need to audit trade table, to see if we are up to date
#!  also log performance (meaning delta between initial func call and end)


class Trade(models.Model):

    # ==== FROM GRYPHON
    trade_id = fields.IntField(pk=True, unique=True)
    unique_id = fields.UUIDField()
    # exchange: fields.ForeignKeyRelation[Exchange] = fields.ForeignKeyField("models.Exchange",
    #                                                                        related_name="trade",
    #                                                                        to_field="name",
    #                                                                        from_field="exchange"
    #                                                                        )
    exchange = fields.ForeignKeyField("models.Exchange", related_name="trades")
    exchange_trade_id = fields.CharField(max_length=30)

    time_created = fields.BigIntField(default=time.time_ns())
    trade_side = fields.CharField(max_length=5)

    pair = fields.CharField(max_length=10)
    price = fields.FloatField()
    volume = fields.FloatField()
    fee = fields.FloatField()
    slippage = fields.FloatField()
    leverage = fields.IntField(default=0)


    # order_id: fields.ForeignKeyRelation[Order] = fields.ForeignKeyField("models.Order",
    #                                                                     related_name="trade",
    #                                                                     to_field="exchange_order_id",
    #                                                                     from_field="order_id"
    #                                                                     )
    order = fields.ForeignKeyField("models.Order", related_name="trades")

    def __str__(self) -> str:
        return f"Trade {self.trade_id}: {self.price}"


