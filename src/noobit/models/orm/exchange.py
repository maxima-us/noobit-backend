from tortoise import fields, models

#! maybe we should also log the uptime for every strategy (every x minutes, we record sthg in a "uptime" table)


class Exchange(models.Model):

    # primary key
    id = fields.SmallIntField(pk=True, generated=False)

    name = fields.CharField(max_length=20)

    # balance = fields.ReverseRelation["models.Balance"]
    # trade = fields.ReverseRelation["models.Trade"]

    def __str__(self) -> str:
        return f"Exchange {self.name}: ID#{self.exchange_id}"
