from server import settings

import typesystem
from starlette.templating import Jinja2Templates

from .items import *
from .users import *

forms = typesystem.Jinja2Forms(directory="templates")
templates = Jinja2Templates(directory="templates")