import random
from tortoise import fields, models

class Strategy(models.Model):

    # surrogate primary key
    spk = fields.SmallIntField(pk=True, generated=True)

    # for discretionary trades, we will assign it the id 0
    # avoid calling any parameter "id": tortoise reserves it for primary keys
    strategy_id = fields.IntField(unique=True, default=random.getrandbits(32))
    # name of strategy
    name = fields.CharField(max_length=15)
    # description of the strategy
    description = fields.TextField(null=True)
    # type of trading the strategy does (eg trend-following, mean-reversion etc)
    type = fields.CharField(max_length=40, null=True)
    timeframe = fields.IntField(null=True)


    # order = fields.ReverseRelation["models.Order"]
