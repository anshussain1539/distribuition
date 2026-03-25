from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from pydantic import BaseModel, Field
from application_context import *
from typing import Optional


router = APIRouter(
    prefix="/supplier-payments",
    tags=["supplier-payments"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


class SupplierPayment(BaseModel):
    supplier_id: str
    amount: float
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


async def generate_payment_id():
    count = supplier_payments_collection.count_documents({})
    return f"SPAY-{count + 1:04d}"


@router.post("/", response_model=dict)
async def pay_supplier(payment: SupplierPayment):
    supplier = suppliers_collection.find_one(
        {"supplier_id": payment.supplier_id}, {"_id": 0}
    )
    if not supplier:
        raise HTTPException(400, detail="Supplier not found")
    if payment.amount <= 0:
        raise HTTPException(400, detail="Amount must be positive")

    payment_dict = payment.model_dump()
    payment_dict["payment_id"] = await generate_payment_id()
    supplier_payments_collection.insert_one(payment_dict)

    # We paid them → reduce what we owe (decreases their balance)
    suppliers_collection.update_one(
        {"supplier_id": payment.supplier_id}, {"$inc": {"balance": -payment.amount}}
    )

    updated = suppliers_collection.find_one(
        {"supplier_id": payment.supplier_id}, {"_id": 0}
    )
    return {
        "payment_id": payment_dict["payment_id"],
        "supplier_id": payment.supplier_id,
        "amount": payment.amount,
        "new_balance": updated.get("balance", 0),
    }


@router.get("/", response_model=dict)
async def list_supplier_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    supplier_id: Optional[str] = Query(None),
):
    skip = (page - 1) * limit
    filter_query = {}
    if supplier_id:
        filter_query["supplier_id"] = supplier_id
    total = supplier_payments_collection.count_documents(filter_query)
    data = list(
        supplier_payments_collection.find(filter_query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return {"data": data, "total": total, "page": page, "limit": limit}
