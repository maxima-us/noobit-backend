import uuid
import datetime
from tortoise import fields, models

from .orders import Order

#!  on startup we need to audit trade table, to see if we are up to date
#!  also log performance (meaning delta between initial func call and end)


class Trade(models.Model):

    # ==== FROM GRYPHON
    trade_id = fields.IntField(pk=True, unique=True)
    unique_id = fields.UUIDField(unique=True, default=uuid.uuid4().hex)
    exchange_id = fields.ForeignKeyField("models.Exchange")
    exchange_trade_id = fields.CharField(max_length=30, unique=True)

    time_created = fields.BigIntField(default=datetime.datetime.utcnow().timestamp())   
    trade_side = fields.CharField(max_length=5)      

    pair = fields.CharField(max_length=10)
    price = fields.FloatField()
    volume = fields.FloatField()
    fee = fields.FloatField()
    slippage = fields.FloatField()
    leverage = fields.IntField(default=0)


    order_id : fields.ForeignKeyRelation[Order] = fields.ForeignKeyField("models.Order", 
                                                                         related_name="trade",
                                                                         to_field="order_id",
                                                                         from_field="trade"
                                                                         )

    
    def __str__(self) -> str:
        return f"Trade {self.trade_id}: {self.price}"


