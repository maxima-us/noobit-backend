import time
from tortoise import fields, models


#!  on startup we need to audit trade table, to see if we are up to date
#!  also log performance (meaning delta between initial func call and end)


class Trade(models.Model):

    # surrogate primary key
    spk = fields.SmallIntField(pk=True, generated=True)

    # id of trade (dependant on exchange)
    # avoid calling any parameter "id": tortoise reserves it for primary keys
    trade_id = fields.CharField(max_length=30)

    # time at which we recorded the trade in db
    time_recorded = fields.BigIntField(default=time.time_ns())

    # side of trade (long, short)
    side = fields.CharField(max_length=5)
    pair = fields.CharField(max_length=10)
    price = fields.FloatField()
    volume = fields.FloatField()
    fee = fields.FloatField()
    slippage = fields.FloatField()
    leverage = fields.IntField(default=0)

    # foreign key relationships (must contain suffix "_id")
    order = fields.ForeignKeyField("models.Order")
    exchange = fields.ForeignKeyField("models.Exchange")
    # order_id: fields.ForeignKeyRelation[Order] = fields.ForeignKeyField("models.Order",
    #                                                                     related_name="trade",
    #                                                                     to_field="exchange_order_id",
    #                                                                     from_field="order_id"
    #                                                                     )
    # exchange: fields.ForeignKeyRelation[Exchange] = fields.ForeignKeyField("models.Exchange",
    #                                                                        related_name="trade",
    #                                                                        to_field="name",
    #                                                                        from_field="exchange"
    #                                                                        )

    def __str__(self) -> str:
        return f"Trade {self.trade_id}: {self.price}"


