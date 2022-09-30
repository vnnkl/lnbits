import json
from http import HTTPStatus
from typing import List

from fastapi import BackgroundTasks, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.params import Depends
from fastapi.templating import Jinja2Templates
from loguru import logger
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse

from lnbits.core.models import User
from lnbits.decorators import check_user_exists  # type: ignore
from lnbits.extensions.diagonalley import diagonalley_ext, diagonalley_renderer
from lnbits.extensions.diagonalley.models import CreateChatMessage
from lnbits.extensions.diagonalley.notifier import Notifier

from .crud import (
    create_chat_message,
    get_diagonalley_market,
    get_diagonalley_market_stalls,
    get_diagonalley_order_details,
    get_diagonalley_products,
    get_diagonalley_stall,
    get_diagonalley_zone,
    get_diagonalley_zones,
    update_diagonalley_product_stock,
)

templates = Jinja2Templates(directory="templates")


@diagonalley_ext.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return diagonalley_renderer().TemplateResponse(
        "diagonalley/index.html", {"request": request, "user": user.dict()}
    )


@diagonalley_ext.get("/stalls/{stall_id}", response_class=HTMLResponse)
async def display(request: Request, stall_id):
    stall = await get_diagonalley_stall(stall_id)
    products = await get_diagonalley_products(stall_id)
    zones = []
    for id in stall.shippingzones.split(","):
        z = await get_diagonalley_zone(id)
        z = z.dict()
        zones.append({"label": z["countries"], "cost": z["cost"], "value": z["id"]})

    if not stall:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Stall does not exist."
        )

    stall = stall.dict()
    del stall["privatekey"]
    stall["zones"] = zones

    return diagonalley_renderer().TemplateResponse(
        "diagonalley/stall.html",
        {
            "request": request,
            "stall": stall,
            "products": [product.dict() for product in products],
        },
    )


@diagonalley_ext.get("/market/{market_id}", response_class=HTMLResponse)
async def display(request: Request, market_id):
    market = await get_diagonalley_market(market_id)

    if not market:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Marketplace doesn't exist."
        )

    stalls = await get_diagonalley_market_stalls(market_id)
    stalls_ids = [stall.id for stall in stalls]
    products = [
        product.dict() for product in await get_diagonalley_products(stalls_ids)
    ]

    return diagonalley_renderer().TemplateResponse(
        "diagonalley/market.html",
        {
            "request": request,
            "market": market,
            "stalls": [stall.dict() for stall in stalls],
            "products": products,
        },
    )


@diagonalley_ext.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, merch: str = Query(...), order: str = Query(...)):
    stall = await get_diagonalley_stall(merch)
    _order = await get_diagonalley_order_details(order)

    return diagonalley_renderer().TemplateResponse(
        "diagonalley/chat.html",
        {
            "request": request,
            "stall": {
                "id": stall.id,
                "name": stall.name,
                "publickey": stall.publickey,
                "wallet": stall.wallet,
            },
            "order": [details.dict() for details in _order],
        },
    )


##################WEBSOCKET ROUTES########################

# Initialize Notifier:
notifier = Notifier()


@diagonalley_ext.websocket("/ws/{room_name}")
async def websocket_endpoint(
    websocket: WebSocket, room_name: str, background_tasks: BackgroundTasks
):
    await notifier.connect(websocket, room_name)
    try:
        while True:
            data = await websocket.receive_text()
            d = json.loads(data)
            d["room_name"] = room_name

            room_members = (
                notifier.get_members(room_name)
                if notifier.get_members(room_name) is not None
                else []
            )

            if websocket not in room_members:
                print("Sender not in room member: Reconnecting...")
                await notifier.connect(websocket, room_name)
                        
            await notifier._notify(data, room_name)

    except WebSocketDisconnect:
        notifier.remove(websocket, room_name)