from fastapi import APIRouter, Form, HTTPException
from fastapi_users.db.tortoise import TortoiseUserDatabase
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

from starlette.requests import Request

from models.orm_models import User as UserModel
from models.data_models import UserDB, User, UserCreate, UserUpdate, UserDBOut

# ======================================================================================

SECRET = "123456789?=test"

auth = JWTAuthentication(secret=SECRET, lifetime_seconds=3600)
user_db = TortoiseUserDatabase(UserDB, UserModel)

# fastapi-users already defines a number of routes, we just need to call them using:
# app.include_router(fastapi_users.router, prefix="/users", tags=["users"])
# in main py file
fastapi_users = FastAPIUsers(user_db, [auth], User, UserCreate, UserUpdate, UserDB, SECRET)

# @fastapi_users.on_after_register()
# async def on_after_register(user: UserModel):
#     print(f"User {user.id} has registered.")


# @fastapi_users.on_after_forgot_password()
# async def on_after_forgot_password(user: UserModel, token: str):
#     print(f"User {user.id} has forgot their password. Reset token: {token}")


# =======================================================================================
# == CUSTOM ROUTES

router = APIRouter()

import asyncio
import httpx
from server.form_schemas import forms, templates, UserRegistrationSchema

@router.get("/register")
async def form_register_user_json(request: Request):
    form = forms.Form(UserRegistrationSchema)
    return templates.TemplateResponse("typesystem_form.html", {"request": request, "form": form})

@router.get("/register_test")
async def form_register_user_fwd(request: Request):
    form = forms.Form(UserRegistrationSchema)
    return templates.TemplateResponse("typesystem_form.html", {"request": request, "form": form})

# default fastapi-users register route takes in json data, not form data, so we need to receive
# form data and pass it along as a POST request attaching json data
@router.post("/register_test", response_model=UserDBOut)
async def signup_user_fwd(*, request: Request):
    data = await asyncio.wait_for(request.form(), timeout=1)
    await httpx.post("http://127.0.0.1:8000/users/register", json={'email': data["email"], 'password': data["password"]})
    created_user = await UserModel.filter(email=data["email"])
    return f"Successfully created user {created_user}"

# adapt fastapi-users register code to take in form data instead of only json
from fastapi_users.password import get_password_hash
from fastapi_users.router import ErrorCode
from starlette import status
import uuid

@router.get("/register_form")
async def form_register_user(request: Request):
    form = forms.Form(UserRegistrationSchema)
    return templates.TemplateResponse("typesystem_form.html", {"request": request, "form": form})

@router.post("/register_form", response_model=UserDBOut)
async def create_register_user(*, email=Form(...), password=Form(...)):
    user_in_db = await UserModel.filter(email=email)

    if user_in_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
                            )

    hashed_password = get_password_hash(password)
    created_user = await UserModel.create(id=str(uuid.uuid4()),
                                          email=email,
                                          hashed_password=hashed_password,
                                          is_active=True,
                                          is_superuser=False,
                                         )
    return created_user
