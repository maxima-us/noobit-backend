import time
from tortoise import fields, models


class Balance(models.Model):

    # surrogate primary key
    spk = fields.SmallIntField(pk=True, generated=True)

    # time at which we took the snapshot
    time_recorded = fields.BigIntField(default=time.time_ns())
    # event responsible for the creation of the record
    event = fields.CharField(max_length=40)

    # current spot holdings
    holdings = fields.JSONField(null=True)
    # current margin positions
    positions = fields.JSONField(null=True)
    # unrealized PnL of positions
    positions_unrealized = fields.FloatField(default=0)

    # holdings - positions
    account_value = fields.FloatField()

    # margin used
    margin = fields.FloatField(default=0)
    # exposure = fields.JSONField(null=True)

    # foreign key relationships (must contain suffix "_id" when referenced)
    exchange = fields.ForeignKeyField("models.Exchange")
    # exchange: fields.ForeignKeyRelation[Exchange] = fields.ForeignKeyField("models.Exchange",
    #                                                                        related_name="balance",
    #                                                                        to_field="id",
    #                                                                        from_field="exchange"
    #                                                                        )

    def __str__(self) -> str:
        return f"Exchange {self.exchange}: {self.holdings}"
