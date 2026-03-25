from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from app.dependencies import templates

router = APIRouter(prefix="/display-payments", tags=["display-payments"])


@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    return templates.TemplateResponse("display_payments.html", {"request": request})
