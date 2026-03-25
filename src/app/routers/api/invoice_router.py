from fastapi import APIRouter, Query
from utils import get_logger
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from pydantic import BaseModel, Field
from application_context import *
from typing import Optional, List


logger = get_logger("invoice router")

router = APIRouter(
    prefix="/invoice",
    tags=["invoice"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


class InvoiceItem(BaseModel):
    item_id: str
    quantity: int
    quantity_free: int = 0  # free items (e.g. 12+2: quantity=12, quantity_free=2)
    price: float
    discount: float = 0.0  # percentage discount on price
    price_discount: float = 0.0  # flat per-unit price discount (amount)


class Invoice(BaseModel):
    shop_id: str
    items: List[InvoiceItem]
    overall_discount: float = 0.0  # percentage discount on total
    total_discount_amount: float = 0.0  # flat amount discount on final bill
    final_total: float
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


def calc_subtotal(inv_item: InvoiceItem) -> float:
    """Subtotal = quantity * price * (1 - discount%) - quantity * price_discount"""
    return (
        inv_item.quantity * inv_item.price * (1 - inv_item.discount / 100)
        - inv_item.quantity * inv_item.price_discount
    )


async def generate_invoice_id():
    count = invoices_collection.count_documents({})
    return f"INV-{count + 1:04d}"


@router.post("/invoices", response_model=dict)
async def create_invoice(invoice: Invoice, deduct_stock: bool = Query(False)):
    if not shops_collection.find_one({"shop_id": invoice.shop_id}):
        raise HTTPException(400, detail="Shop not found")

    total_before = 0
    for inv_item in invoice.items:
        db_item = items_collection.find_one({"item_id": inv_item.item_id})
        if not db_item:
            raise HTTPException(400, detail=f"Item {inv_item.item_id} not found")
        total_qty = inv_item.quantity + inv_item.quantity_free
        if deduct_stock and db_item.get("stock", 0) < total_qty:
            raise HTTPException(
                400, detail=f"Insufficient stock for {inv_item.item_id}"
            )
        total_before += calc_subtotal(inv_item)

    discount_amount = total_before * (invoice.overall_discount / 100)
    expected_total = total_before - discount_amount - invoice.total_discount_amount
    if abs(invoice.final_total - expected_total) > 0.01:
        raise HTTPException(400, detail="Total mismatch")

    invoice_dict = invoice.model_dump()
    invoice_dict["invoice_id"] = await generate_invoice_id()

    if deduct_stock:
        invoice_dict["status"] = "completed"
        for inv_item in invoice.items:
            total_qty = inv_item.quantity + inv_item.quantity_free
            items_collection.update_one(
                {"item_id": inv_item.item_id}, {"$inc": {"stock": -total_qty}}
            )
        # Add final_total to shop balance (shop owes us)
        shops_collection.update_one(
            {"shop_id": invoice.shop_id}, {"$inc": {"balance": invoice.final_total}}
        )

    invoices_collection.insert_one(invoice_dict)
    return {"invoice_id": invoice_dict["invoice_id"], "status": invoice_dict["status"]}


@router.get("/invoices/{invoice_id}", response_model=dict)
async def get_invoice(invoice_id: str):
    inv = invoices_collection.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, detail="Invoice not found")
    return inv


@router.get("/invoices", response_model=dict)
async def list_invoices(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(draft|completed)$"),
):
    skip = (page - 1) * limit
    filter_query = {}
    if status:
        filter_query["status"] = status

    total = invoices_collection.count_documents(filter_query)
    data = list(
        invoices_collection.find(filter_query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "filtered_by_status": status or "all",
    }


@router.post("/invoices/{invoice_id}/complete")
async def complete_invoice(invoice_id: str):
    inv = invoices_collection.find_one({"invoice_id": invoice_id})
    if not inv:
        raise HTTPException(404, detail="Invoice not found")
    if inv["status"] != "draft":
        raise HTTPException(400, detail="Invoice is not a draft")

    for item in inv["items"]:
        total_qty = item["quantity"] + item.get("quantity_free", 0)
        result = items_collection.update_one(
            {"item_id": item["item_id"], "stock": {"$gte": total_qty}},
            {"$inc": {"stock": -total_qty}},
        )
        if result.modified_count == 0:
            raise HTTPException(
                400, detail=f"Insufficient stock for item {item['item_id']}"
            )

    invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"status": "completed", "updated_at": datetime.now()}},
    )

    # Add final_total to shop balance
    shops_collection.update_one(
        {"shop_id": inv["shop_id"]}, {"$inc": {"balance": inv["final_total"]}}
    )

    return {"message": "Invoice completed and stock deducted"}


@router.put("/invoices/{invoice_id}", response_model=dict)
async def update_invoice(invoice_id: str, invoice: Invoice):
    existing = invoices_collection.find_one({"invoice_id": invoice_id})
    if not existing:
        raise HTTPException(404, detail="Invoice not found")
    if existing["status"] != "draft":
        raise HTTPException(400, detail="Can only update drafts")

    if not shops_collection.find_one({"shop_id": invoice.shop_id}):
        raise HTTPException(400, detail="Shop not found")

    total_before = 0
    for inv_item in invoice.items:
        db_item = items_collection.find_one({"item_id": inv_item.item_id})
        if not db_item:
            raise HTTPException(400, detail=f"Item {inv_item.item_id} not found")
        total_before += calc_subtotal(inv_item)

    discount_amount = total_before * (invoice.overall_discount / 100)
    expected_total = total_before - discount_amount - invoice.total_discount_amount
    if abs(invoice.final_total - expected_total) > 0.01:
        raise HTTPException(400, detail="Total mismatch")

    invoice_dict = invoice.model_dump()
    invoice_dict["invoice_id"] = invoice_id
    invoice_dict["updated_at"] = datetime.now()
    invoice_dict["status"] = "draft"

    invoices_collection.replace_one({"invoice_id": invoice_id}, invoice_dict)
    return {"message": "Invoice updated successfully", "invoice_id": invoice_id}
