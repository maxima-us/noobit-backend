from fastapi_users import models

# FastAPI-Users models

class User(models.BaseUser):
    pass


class UserCreate(User, models.BaseUserCreate):
    pass


class UserUpdate(User, models.BaseUserUpdate):
    pass


class UserDB(User, models.BaseUserDB):
    pass


# Our own response model to filter out password and id

from pydantic import BaseModel, EmailStr


class UserDBOut(BaseModel):
    email: EmailStr
    id: str

    class Config:
        orm_mode = True
