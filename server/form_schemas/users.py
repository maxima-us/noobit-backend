import typesystem

class UserRegistrationSchema(typesystem.Schema):
    email = typesystem.String(title="email", max_length=50, format="email", description="user@domain.extension")
    password = typesystem.String(title="password", max_length=40, format="password")
    confirm_password = typesystem.String(title= "confirm_password", max_length=40, format="password")
