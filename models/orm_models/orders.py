import datetime
import uuid
from tortoise import fields, models
from .strategy import Strategy

#!  on startup we need to audit order table, to see if we are up to date
#!  also log performance (meaning delta between initial func call and end)


class Order(models.Model):

    # ==== FROM GRYPHON
    order_id = fields.IntField(pk=True, unique=True)
    unique_id = fields.UUIDField(unique=True)           # setting to default does not work
    exchange_id = fields.ForeignKeyField("models.Exchange")
    exchange_order_id = fields.CharField(max_length=20, unique=True)

    status = fields.CharField(max_length=30, default="pending")
    order_type = fields.CharField(max_length=30)
    order_side = fields.CharField(max_length=5)
    
    time_created = fields.BigIntField(default=datetime.datetime.utcnow().timestamp())                             #should be unix timestamp
    time_executed = fields.BigIntField(null=True)                   

    pair = fields.CharField(max_length=10)
    volume = fields.FloatField()
    filled = fields.FloatField()
    price = fields.FloatField(null=True)
    price2 = fields.FloatField(null=True)
    leverage = fields.SmallIntField(null=True) 

    start_time = fields.BigIntField(null=True)
    expire_time = fields.BigIntField(null=True)
    
    strategy_id : fields.ForeignKeyRelation[Strategy] = fields.ForeignKeyField("models.Strategy", 
                                                                         related_name="order",
                                                                         to_field="strategy_id"
                                                                         )

    # trades  = relatinship ... ??? how to handle in tortoise
    trade = fields.ReverseRelation["models.Trade"]


    def __str__(self) -> str:
        return f"Order {self.order_id}: {self.price}"
