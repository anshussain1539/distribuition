"""The main fastapi app module"""

import os
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from utils import get_logger
from app.routers import (
    index,
    bulk,
    display_items,
    invoice,
    display_invoices,
    purchase_invoice,
    receive_payment,
    display_purchase_invoices,
    display_payments,
    analytics_view,
    pay_supplier,
    display_supplier_payments,
)
from app.routers.api import user
from app.routers.api import index as api_index
from app.routers.api import (
    bulk_router,
    invoice_router,
    purchase_router,
    payment_router,
    analytics_router,
    supplier_payment_router,
)

logger = get_logger("main")

app = FastAPI(
    title="Distribution Management",
    description="Distribution Management System",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redocs",
)


def apply_origins(application: FastAPI):
    origins = os.getenv("ORIGINS", "*")
    origins_lst = origins.split(",")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins_lst,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return origins


origins_applied = apply_origins(app)
app.mount("/public", StaticFiles(directory="../public"), name="public")
logger.info(f"Accepting from origins {origins_applied}")

# HTML view routers
app.include_router(index.router)
app.include_router(bulk.router)
app.include_router(display_items.router)
app.include_router(invoice.router)
app.include_router(display_invoices.router)
app.include_router(purchase_invoice.router)
app.include_router(receive_payment.router)
app.include_router(display_purchase_invoices.router)
app.include_router(display_payments.router)
app.include_router(analytics_view.router)
app.include_router(pay_supplier.router)
app.include_router(display_supplier_payments.router)

# API routers
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(api_index.router)
api_v1_router.include_router(user.router)
api_v1_router.include_router(bulk_router.router)
api_v1_router.include_router(invoice_router.router)
api_v1_router.include_router(purchase_router.router)
api_v1_router.include_router(payment_router.router)
api_v1_router.include_router(analytics_router.router)
api_v1_router.include_router(supplier_payment_router.router)

app.include_router(api_v1_router)
