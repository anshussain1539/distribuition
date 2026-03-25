from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from app.dependencies import templates


router = APIRouter(
    prefix="/receive-payment",
    tags=["receive-payment"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


@router.get("/", response_class=HTMLResponse)
async def receive_payment_page(request: Request):
    return templates.TemplateResponse("receive_payment.html", {"request": request})
