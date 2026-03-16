import asyncio

from fastapi import APIRouter
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import orangepiller_ext_generic
from .views_api import orangepiller_ext_api

orangepiller_ext: APIRouter = APIRouter(prefix="/orangepiller", tags=["orangepiller"])
orangepiller_ext.include_router(orangepiller_ext_generic)
orangepiller_ext.include_router(orangepiller_ext_api)

orangepiller_static_files = [
    {
        "path": "/orangepiller/static",
        "name": "orangepiller_static",
    }
]

scheduled_tasks: list[asyncio.Task] = []


def orangepiller_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def orangepiller_start():
    from lnbits.tasks import create_permanent_unique_task

    task = create_permanent_unique_task("ext_orangepiller", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = [
    "db",
    "orangepiller_ext",
    "orangepiller_ext_api",
    "orangepiller_start",
    "orangepiller_static_files",
    "orangepiller_stop",
]
