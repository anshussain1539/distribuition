from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from pydantic import BaseModel, Field
from application_context import *
from typing import Optional, List


router = APIRouter(
    prefix="/purchase",
    tags=["purchase"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


class PurchaseItem(BaseModel):
    item_id: str
    quantity: int
    price: float = 0.0


class PurchaseInvoice(BaseModel):
    supplier_id: str  # required, must exist in suppliers_collection
    items: List[PurchaseItem]
    total: float
    notes: Optional[str] = None
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


async def generate_purchase_id():
    count = purchase_invoices_collection.count_documents({})
    return f"PINV-{count + 1:04d}"


@router.post("/invoices", response_model=dict)
async def create_purchase_invoice(
    invoice: PurchaseInvoice, add_stock: bool = Query(False)
):
    if not suppliers_collection.find_one({"supplier_id": invoice.supplier_id}):
        raise HTTPException(400, detail="Supplier not found")

    for p_item in invoice.items:
        if not items_collection.find_one({"item_id": p_item.item_id}):
            raise HTTPException(400, detail=f"Item {p_item.item_id} not found")

    invoice_dict = invoice.model_dump()
    invoice_dict["invoice_id"] = await generate_purchase_id()

    if add_stock:
        invoice_dict["status"] = "completed"
        for p_item in invoice.items:
            items_collection.update_one(
                {"item_id": p_item.item_id}, {"$inc": {"stock": p_item.quantity}}
            )
        # We owe the supplier → increase their balance
        suppliers_collection.update_one(
            {"supplier_id": invoice.supplier_id}, {"$inc": {"balance": invoice.total}}
        )

    purchase_invoices_collection.insert_one(invoice_dict)
    return {"invoice_id": invoice_dict["invoice_id"], "status": invoice_dict["status"]}


@router.get("/invoices", response_model=dict)
async def list_purchase_invoices(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(draft|completed)$"),
):
    skip = (page - 1) * limit
    filter_query = {}
    if status:
        filter_query["status"] = status
    total = purchase_invoices_collection.count_documents(filter_query)
    data = list(
        purchase_invoices_collection.find(filter_query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return {"data": data, "total": total, "page": page, "limit": limit}


@router.get("/invoices/{invoice_id}", response_model=dict)
async def get_purchase_invoice(invoice_id: str):
    inv = purchase_invoices_collection.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, detail="Purchase invoice not found")
    return inv


@router.put("/invoices/{invoice_id}", response_model=dict)
async def update_purchase_invoice(invoice_id: str, invoice: PurchaseInvoice):
    existing = purchase_invoices_collection.find_one({"invoice_id": invoice_id})
    if not existing:
        raise HTTPException(404, detail="Purchase invoice not found")
    if existing["status"] != "draft":
        raise HTTPException(400, detail="Can only update drafts")

    if not suppliers_collection.find_one({"supplier_id": invoice.supplier_id}):
        raise HTTPException(400, detail="Supplier not found")

    for p_item in invoice.items:
        if not items_collection.find_one({"item_id": p_item.item_id}):
            raise HTTPException(400, detail=f"Item {p_item.item_id} not found")

    invoice_dict = invoice.model_dump()
    invoice_dict["invoice_id"] = invoice_id
    invoice_dict["updated_at"] = datetime.now()
    invoice_dict["status"] = "draft"
    purchase_invoices_collection.replace_one({"invoice_id": invoice_id}, invoice_dict)
    return {"message": "Updated", "invoice_id": invoice_id}


@router.post("/invoices/{invoice_id}/complete")
async def complete_purchase_invoice(invoice_id: str):
    inv = purchase_invoices_collection.find_one({"invoice_id": invoice_id})
    if not inv:
        raise HTTPException(404, detail="Purchase invoice not found")
    if inv["status"] != "draft":
        raise HTTPException(400, detail="Invoice is not a draft")

    for item in inv["items"]:
        items_collection.update_one(
            {"item_id": item["item_id"]}, {"$inc": {"stock": item["quantity"]}}
        )

    purchase_invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"status": "completed", "updated_at": datetime.now()}},
    )

    # We owe the supplier → increase their balance
    suppliers_collection.update_one(
        {"supplier_id": inv["supplier_id"]}, {"$inc": {"balance": inv["total"]}}
    )

    return {"message": "Purchase invoice completed and stock added"}
