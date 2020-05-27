from tortoise import fields, models


from noobit.models.orm.orders import Order


#!  on startup we need to audit trade table, to see if we are up to date
#!  also log performance (meaning delta between initial func call and end)


class Trade(models.Model):

    # surrogate primary key
    spk = fields.SmallIntField(pk=True, generated=True)

    trdMatchID = fields.CharField(max_length=50, null=True)
    # orderID = fields.ForeignKeyField("models.Order")
    clOrdID = fields.CharField(max_length=50, null=True)

    symbol = fields.CharField(max_length=20, null=True)
    side = fields.CharField(max_length=20, null=True)
    ordType = fields.CharField(max_length=20, null=True)
    avgPx = fields.FloatField(null=True)
    cumQty = fields.FloatField()
    grossTradeAmt = fields.FloatField()
    commission = fields.FloatField()
    transactTime = fields.BigIntField(null=True)
    tickDirection = fields.FloatField(null=True)

    # remember to convert this to json when we write to db
    # pydantic model just defines it as Any
    text = fields.JSONField(null=True)

    # foreign key relationships (must contain suffix "_id")
    exchange = fields.ForeignKeyField("models.Exchange")
    orderID: fields.ForeignKeyRelation[Order] = fields.ForeignKeyField("models.Order",
                                                                       related_name="trade",
                                                                       to_field="orderID",
                                                                       from_field="orderID"
                                                                       )
    # exchange: fields.ForeignKeyRelation[Exchange] = fields.ForeignKeyField("models.Exchange",
    #                                                                        related_name="trade",
    #                                                                        to_field="name",
    #                                                                        from_field="exchange"
    #                                                                        )

    def __str__(self) -> str:
        return f"Trade {self.trade_id}: {self.price}"


