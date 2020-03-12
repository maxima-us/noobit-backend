from tortoise import fields, models


class Item(models.Model):

    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=40)
    description = fields.CharField(max_length=120)
    owner_id = fields.CharField(max_length=40)

    def __str__(self) -> str:
        return f"Item {self.id}: {self.title}"