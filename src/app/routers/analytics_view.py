from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from app.dependencies import templates

router = APIRouter(prefix="/analytics-view", tags=["analytics-view"])


@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})
