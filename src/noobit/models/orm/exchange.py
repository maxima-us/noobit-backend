from tortoise import fields, models

#! maybe we should also log the uptime for every strategy (every x minutes, we record sthg in a "uptime" table)


class Exchange(models.Model):

    exchange_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=20)

    # balance = fields.ReverseRelation["models.Balance"]
    # trade = fields.ReverseRelation["models.Trade"]

    def __str__(self) -> str:
        return f"Exchange {self.name}: ID#{self.exchange_id}"
