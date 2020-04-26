import time
from tortoise import fields, models

#!  on startup we need to audit order table, to see if we are up to date
#!  also log performance (meaning delta between initial func call and end)


class Order(models.Model):

    # surrogate primary key
    spk = fields.SmallIntField(pk=True, generated=True)

    # id of order (dependant on exchange)
    # avoid calling any parameter "id": tortoise reserves it for primary keys
    order_id = fields.CharField(max_length=30)
    pair = fields.CharField(max_length=10)
    # status of order (pending, open, cancelled, filled)
    status = fields.CharField(max_length=30, default="pending")
    # type of order (market, limit, takeprofit, stoploss)
    type = fields.CharField(max_length=30)
    # side or order (long, short)
    side = fields.CharField(max_length=5)

    time_open = fields.BigIntField()
    time_start = fields.BigIntField(null=True)
    time_expire = fields.BigIntField(null=True)
    # time at which the order was recorded in the db
    time_recorded = fields.BigIntField(default=time.time_ns())
    # time at which order has been completely filled
    time_executed = fields.BigIntField(null=True)

    # total volume of the order
    volume_total = fields.FloatField()
    # volume that was filled so far
    volume_filled = fields.FloatField()
    # limit entry price (if market than it will be 0)
    price_limit = fields.FloatField(null=True)
    # take profit price
    price_tp = fields.FloatField(null=True)
    # stop loss price
    price_sl = fields.FloatField(null=True)
    # average fill price for order
    price_avg_fill = fields.FloatField(null=True)
    leverage = fields.SmallIntField(null=True)


    # foreign key relationships (must contain suffix "_id")
    exchange = fields.ForeignKeyField("models.Exchange")
    strategy = fields.ForeignKeyField("models.Strategy")
    # strategy_id: fields.ForeignKeyRelation[Strategy] = fields.ForeignKeyField("models.Strategy",
    #                                                                           related_name="order",
    #                                                                           to_field="id",
    #                                                                           from_field="order"
    #                                                                           )

    # trades  = relatinship ... ??? how to handle in tortoise
    # trade = fields.ReverseRelation["models.Trade"]


    def __str__(self) -> str:
        return f"Order {self.order_id}: {self.price}"
