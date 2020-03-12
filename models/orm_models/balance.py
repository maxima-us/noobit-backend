from tortoise import fields, models
from .exchange import Exchange


class Balance(models.Model):

    # exchange = fields.ForeignKeyField('models.Exchange')
    holdings = fields.JSONField(null=True)
    
    # not yet generated, need to write startup code before
    # whenever adding a new column, we will need to delete the entire table in the db
    positions = fields.JSONField(null=True)               
    
    exchange : fields.ForeignKeyRelation[Exchange] = fields.ForeignKeyField("models.Exchange", 
                                                                            related_name="balance",
                                                                            to_field="name"
                                                                            )

    def __str__(self) -> str:
        return f"Exchange {self.exchange}: {self.holdings}"