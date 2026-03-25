from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from pydantic import BaseModel, Field
from application_context import *
from typing import Optional


router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


class Payment(BaseModel):
    shop_id: str
    amount: float
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


async def generate_payment_id():
    count = payments_collection.count_documents({})
    return f"PAY-{count + 1:04d}"


@router.post("/", response_model=dict)
async def receive_payment(payment: Payment):
    shop = shops_collection.find_one({"shop_id": payment.shop_id}, {"_id": 0})
    if not shop:
        raise HTTPException(400, detail="Shop not found")
    if payment.amount <= 0:
        raise HTTPException(400, detail="Amount must be positive")

    payment_dict = payment.model_dump()
    payment_dict["payment_id"] = await generate_payment_id()
    payments_collection.insert_one(payment_dict)

    # Deduct from shop balance (shop paid us)
    shops_collection.update_one(
        {"shop_id": payment.shop_id}, {"$inc": {"balance": -payment.amount}}
    )

    updated_shop = shops_collection.find_one({"shop_id": payment.shop_id}, {"_id": 0})
    return {
        "payment_id": payment_dict["payment_id"],
        "shop_id": payment.shop_id,
        "amount": payment.amount,
        "new_balance": updated_shop.get("balance", 0),
    }


@router.get("/", response_model=dict)
async def list_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    shop_id: Optional[str] = Query(None),
):
    skip = (page - 1) * limit
    filter_query = {}
    if shop_id:
        filter_query["shop_id"] = shop_id
    total = payments_collection.count_documents(filter_query)
    data = list(
        payments_collection.find(filter_query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return {"data": data, "total": total, "page": page, "limit": limit}
