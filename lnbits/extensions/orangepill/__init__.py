from .tasks import wait_for_paid_invoices
import asyncio

from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from lnbits.db import Database
from lnbits.helpers import template_renderer
from lnbits.tasks import catch_everything_and_restart

db = Database("ext_orangepill")

orangepill_static_files = [
    {
        "path": "/orangepill/static",
        "app": StaticFiles(packages=[("lnbits", "extensions/orangepill/static")]),
        "name": "orangepill_static",
    }
]

orangepill_ext: APIRouter = APIRouter(
    prefix="/orangepill", tags=["orangepill"])


def orangepill_renderer():
    return template_renderer(["lnbits/extensions/orangepill/templates"])


from .lnurl import *  # noqa
from .views import *  # noqa
from .views_api import *  # noqa


def orangepill_start():
    loop = asyncio.get_event_loop()
    loop.create_task(catch_everything_and_restart(wait_for_paid_invoices))
