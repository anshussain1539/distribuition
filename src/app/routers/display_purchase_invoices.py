from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from app.dependencies import templates

router = APIRouter(
    prefix="/display-purchase-invoices", tags=["display-purchase-invoices"]
)


@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    return templates.TemplateResponse(
        "display_purchase_invoices.html", {"request": request}
    )
