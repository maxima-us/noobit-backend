import datetime
from tortoise import fields, models
from .exchange import Exchange


class Balance(models.Model):

    # time at which we took the snapshot
    time_recorded = fields.BigIntField(default=datetime.datetime.utcnow().timestamp())
    # event responsible for the creation of the record
    event = fields.CharField(max_length=40)

    holdings = fields.JSONField(null=True)
    positions = fields.JSONField(null=True)
    # unrealized PnL of positions
    positions_unrealized = fields.FloatField(default=0)

    # holdings - positions
    account_value = fields.FloatField()

    # margin
    margin = fields.FloatField(default=0)
    exposure = fields.JSONField(null=True)

    exchange: fields.ForeignKeyRelation[Exchange] = fields.ForeignKeyField("models.Exchange",
                                                                           related_name="balance",
                                                                           to_field="name",
                                                                           from_field="exchange"
                                                                           )

    def __str__(self) -> str:
        return f"Exchange {self.exchange}: {self.holdings}"
