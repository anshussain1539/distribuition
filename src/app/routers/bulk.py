"""Index page / for the application
this is a non api HTML reponse router
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from app.dependencies import templates


router = APIRouter(
    prefix="/bulk-upload",
    tags=["bulk-upload"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("bulk.html", {"request": request, "data": 10})
