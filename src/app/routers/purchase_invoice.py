from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from app.dependencies import templates


router = APIRouter(
    prefix="/purchase-invoice",
    tags=["purchase-invoice"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


@router.get("/", response_class=HTMLResponse)
async def purchase_invoice_page(request: Request):
    return templates.TemplateResponse("purchase_invoice.html", {"request": request})
