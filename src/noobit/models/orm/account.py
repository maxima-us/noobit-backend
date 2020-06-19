from tortoise import fields, models


class Account(models.Model):

    # surrogate primary key
    spk = fields.SmallIntField(pk=True, generated=True)

    # time at which we took the snapshot
    time_recorded = fields.DatetimeField(auto_now=True)
    # event responsible for the creation of the record
    event = fields.CharField(max_length=40)

    balances = fields.JSONField()
    exposure = fields.JSONField(null=True)
    open_positions = fields.JSONField(null=True)

    # foreign key relationships (must contain suffix "_id" when referenced)
    exchange = fields.ForeignKeyField("models.Exchange")
    # exchange: fields.ForeignKeyRelation[Exchange] = fields.ForeignKeyField("models.Exchange",
    #                                                                        related_name="balance",
    #                                                                        to_field="id",
    #                                                                        from_field="exchange"
    #                                                                        )

    def __str__(self) -> str:
        return f"Exchange {self.exchange}: {self.holdings}"
