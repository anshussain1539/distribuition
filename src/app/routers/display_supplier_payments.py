from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from app.dependencies import templates

router = APIRouter(
    prefix="/display-supplier-payments", tags=["display-supplier-payments"]
)


@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    return templates.TemplateResponse(
        "display_supplier_payments.html", {"request": request}
    )
