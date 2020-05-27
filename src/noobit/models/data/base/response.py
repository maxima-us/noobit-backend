from typing import Union, Any

import ujson
from pydantic import BaseModel, conint
from starlette import status
from starlette.responses import JSONResponse


# ================================================================================


class NoobitResponse(BaseModel):
    """Base Noobit Response Model

    Args:
        status_code (int): http/ws code
        value (typing.Any): contains data of the response

    Returns:
        pydantic.BaseModel
    """
    status_code: conint(ge=100, le=1000)
    value: Any


class OKResponse(NoobitResponse):
    """Noobit Response Model indicating success

    Args:
        status_code (int): http/ws code
        value (typing.Any): contains data of the response

    Attributes:
        is_ok (bool): True
        is_error (bool): False

    Returns:
        pydantic.BaseModel
    """
    is_ok: bool = True
    is_error: bool = False


class ErrorResponse(NoobitResponse):
    """Noobit Response Model indicating error

    Args:
        status_code (int): http/ws code
        value (typing.Any): contains data of the response

    Attributes:
        is_ok (bool): False
        is_error (bool): True

    Returns:
        pydantic.BaseModel
    """

    is_ok: bool = False
    is_error: bool = True


# ================================================================================

#! to serialize datetime to string ???
#! ==> Not sure this is actually a great idea
class NoobitUJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        assert ujson is not None, "ujson must be installed to use UJSONResponse"
        return ujson.dumps(content, ensure_ascii=False).encode("utf-8")