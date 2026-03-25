from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from app.dependencies import templates

router = APIRouter(prefix="/pay-supplier", tags=["pay-supplier"])


@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    return templates.TemplateResponse("pay_supplier.html", {"request": request})
