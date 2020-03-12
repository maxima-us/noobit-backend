import typesystem

class ItemSchema(typesystem.Schema):
    form_title = typesystem.String(title="title", max_length=40)
    form_descr = typesystem.String(title="description", max_length=120, default=str("Enter description of a weapon"))
    form_owner = typesystem.String(title="owner", max_length=40)
