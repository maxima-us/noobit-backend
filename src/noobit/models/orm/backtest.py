from tortoise import fields, models


class Backtest(models.Model):

    name = fields.CharField(max_length=50)
    description = fields.TextField()

    exchange = fields.CharField(max_length=40)
    symbol = fields.CharField(max_length=20)
    timeframe = fields.SmallIntField()
    performance = fields.JSONField()
    parameters = fields.JSONField()
