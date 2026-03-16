from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

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
