import datetime
from tortoise import fields, models
from .strategy import Strategy

#!  on startup we need to audit order table, to see if we are up to date
#!  also log performance (meaning delta between initial func call and end)


class Order(models.Model):

    # ==== FROM GRYPHON
    # order_id = fields.IntField(unique=True)
    order_id = fields.CharField(pk=True, max_length=30)
    unique_id = fields.UUIDField()           # setting to default does not work
    exchange_id = fields.ForeignKeyField("models.Exchange", related_name="orders")
    pair = fields.CharField(max_length=10)

    status = fields.CharField(max_length=30, default="pending")
    type = fields.CharField(max_length=30)
    side = fields.CharField(max_length=5)

    start_time = fields.BigIntField(null=True)
    expire_time = fields.BigIntField(null=True)
    time_created = fields.BigIntField(default=datetime.datetime.utcnow().timestamp())                             #should be unix timestamp
    time_executed = fields.BigIntField(null=True)

    volume_total = fields.FloatField()
    volume_filled = fields.FloatField()
    # limit entry price
    price_limit = fields.FloatField(null=True)
    # take profit price
    price_tp = fields.FloatField(null=True)
    # stop loss price
    price_sl = fields.FloatField(null=True)
    # average fill price for order
    price_avg_fill = fields.FloatField(null=True)
    leverage = fields.SmallIntField(null=True)


    strategy_id: fields.ForeignKeyRelation[Strategy] = fields.ForeignKeyField("models.Strategy",
                                                                              related_name="order",
                                                                              to_field="id",
                                                                              from_field="order"
                                                                              )

    # trades  = relatinship ... ??? how to handle in tortoise
    # trade = fields.ReverseRelation["models.Trade"]


    def __str__(self) -> str:
        return f"Order {self.order_id}: {self.price}"
