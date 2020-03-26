import random
from tortoise import fields, models
from .exchange import Exchange

class Strategy(models.Model):

    # for discretionary trades, we will assign it the id 0

    id = fields.IntField(pk=True, unique=True, default=random.getrandbits(32))
    name = fields.CharField(max_length=15)
    type = fields.CharField(max_length=40, null=True)
    timeframe = fields.IntField(null=True)
    
    
    order = fields.ReverseRelation["models.Order"]

