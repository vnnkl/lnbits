from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

from .crud import get_arrangement

orangepiller_ext_generic = APIRouter(tags=["orangepiller"])


@orangepiller_ext_generic.get(
    "/", description="Orange Piller extension", response_class=HTMLResponse
)
async def index(
    request: Request,
    user: User = Depends(check_user_exists),
):
    return template_renderer(["orangepiller/templates"]).TemplateResponse(
        request, "orangepiller/index.html", {"user": user.json()}
    )


@orangepiller_ext_generic.get(
    "/poster/{arrangement_id}",
    description="Printable poster with merchant QR code",
    response_class=HTMLResponse,
)
async def poster(request: Request, arrangement_id: str):
    arrangement = await get_arrangement(arrangement_id)
    if arrangement is None or arrangement.tpos_url is None:
        raise HTTPException(status_code=404, detail="Arrangement not found")
    poster_data = {
        "merchant_name": arrangement.merchant_name or "Merchant",
        "tpos_url": arrangement.tpos_url,
        "arrangement_id": arrangement.id,
    }
    return template_renderer(["orangepiller/templates"]).TemplateResponse(
        request,
        "orangepiller/poster.html",
        {"poster_data": poster_data},
    )
