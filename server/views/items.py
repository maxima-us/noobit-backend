from fastapi import APIRouter, Form
from fastapi.encoders import jsonable_encoder

from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.status import HTTP_201_CREATED

# from data_models.items import Item
from models.orm_models.items import Item


router = APIRouter()

# ====================================================================================

@router.get("/", name="home")
async def read_items():
    return [
        {"name": "Item FOO"},
        {"name": "Item BAR"},
        ]


@router.get("/item/{item_id}")
async def read_item(item_id: str):
    return {"name": "Fake Specific Item", "item_id": item_id}


@router.get("/starlette/item/{item_id}")
async def read_item_starlette(request: Request):
    data = {"name": "Starlette Response", "request_id": request.path_params["item_id"]}
    json_data = jsonable_encoder(data)
    return JSONResponse(content=json_data)


@router.get("/starlette/all_items")
async def all_items():
    all_items = await Item.all()

    return all_items


# Starlette way of doing it
@router.post("/starlette/form/create_ts")
async def add_item_starlette(request: Request):

    data = await request.form()
    # posted_id = data["form_id"]
    posted_title = data["form_title"]
    posted_description = data["form_descr"]
    posted_owner = data["form_owner"]

    item = await Item.create(
        title=posted_title,
        description=posted_description,
        owner_id=posted_owner,
        )
    return JSONResponse({"item": str(item)}, status_code=HTTP_201_CREATED)

# FastAPI way of doing it
@router.post("/fastapi/form/create_ts")
async def add_item_fastapi(*, form_title=Form(...), form_descr=Form(...), form_owner=Form(...)):
    item = await Item.create(
        title=form_title,
        description=form_descr,
        owner_id=form_owner
    )
    return JSONResponse({"item": str(item)}, status_code=HTTP_201_CREATED)

# =======================================================================================
# == USING STARLETTE TEMPLATING SYSTEM

from starlette.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")


@router.get("/starlette/form/create")
async def item_form(request: Request):
    return templates.TemplateResponse("item_form.html", {"request": request})


# ======================================================================================
# == USING FORM SYSTEM

from server.form_schemas import forms, ItemSchema

@router.get("/starlette/form/create_ts")
async def item_form_starlette(request: Request):
    form = forms.Form(ItemSchema)
    return templates.TemplateResponse("typesystem_form.html", {"request": request, "form": form})


@router.get("/fastapi/form/create_ts")
async def item_form_fastapi(request: Request):
    form = forms.Form(ItemSchema)
    return templates.TemplateResponse("typesystem_form.html", {"request": request, "form": form})
