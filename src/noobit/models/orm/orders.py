from tortoise import fields, models

from noobit.models.orm.strategy import Strategy


#!  on startup we need to audit order table, to see if we are up to date
#!  also log performance (meaning delta between initial func call and end)

# ORDER ORM Model that conforms to our pydantic response model
# We should always validate and serialize with pydantic before writing to db
class Order(models.Model):

    # surrogate primary key
    spk = fields.SmallIntField(pk=True, generated=True)

    # id of order (dependant on exchange)
    # avoid calling any parameter "id": tortoise reserves it for primary keys
    # fields need to be unique for it to be a reverse relation to a FK
    orderID = fields.CharField(max_length=30, unique=True)

    symbol = fields.CharField(max_length=10)
    currency = fields.CharField(max_length=10)
    side = fields.CharField(max_length=5)
    ordType = fields.CharField(max_length=30)
    execInst = fields.CharField(max_length=20, null=True)

    clOrdID = fields.CharField(max_length=30, null=True)
    account = fields.CharField(max_length=30, null=True)
    cashMargin = fields.CharField(max_length=10)

    ordStatus = fields.CharField(max_length=30, default="new")

    workingIndicator = fields.BooleanField()
    ordRejReason = fields.CharField(max_length=100, null=True)

    timeInForce = fields.CharField(max_length=20, null=True)
    transactTime = fields.BigIntField(null=True)
    sendingTime = fields.BigIntField(null=True)
    effectiveTime = fields.BigIntField(null=True)
    validUntilTime = fields.BigIntField(null=True)
    expireTime = fields.BigIntField(null=True)

    displayQty = fields.FloatField(null=True)
    grossTradeAmt = fields.FloatField(null=True)
    orderQty = fields.FloatField(null=True)
    cashOrderQty = fields.FloatField(null=True)
    orderPercent = fields.IntField(null=True)
    cumQty = fields.FloatField(null=True)
    leavesQty = fields.FloatField(null=True)
    commission = fields.FloatField(null=True)

    price = fields.FloatField(null=True)
    stopPx = fields.FloatField(null=True)
    avgPx = fields.FloatField(null=True)

    marginRatio = fields.FloatField()
    marginAmt = fields.FloatField()
    realisedPnL = fields.FloatField()
    unrealisedPnL = fields.FloatField()

    # be careful since pydantic model is a list of Fill Models
    fills = fields.JSONField(null=True)

    text = fields.JSONField(null=True)

    # targetStrategy = fields.ForeignKeyField("models.Strategy")
    targetStrategy: fields.ForeignKeyRelation[Strategy] = fields.ForeignKeyField("models.Strategy",
                                                                       related_name="trade",
                                                                       to_field="strategy_id",
                                                                       from_field="targetStrategy"
                                                                       )
    targetStrategyParameters = fields.JSONField(null=True)

    # foreign key relationships (must contain suffix "_id" when referencing)
    exchange = fields.ForeignKeyField("models.Exchange")

    # trades  = relatinship ... ??? how to handle in tortoise
    trade = fields.ReverseRelation["models.Trade"]


