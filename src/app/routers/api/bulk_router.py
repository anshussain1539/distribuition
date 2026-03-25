""" Bulk upload and CRUD router for shops, items, and suppliers """

from fastapi import APIRouter, Query
from utils import get_logger
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ValidationError
from application_context import *
from typing import Optional


logger = get_logger("api index")

router = APIRouter(
    prefix="/bulk",
    tags=["bulk"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


# ── Models ────────────────────────────────────────────────────────────────────


class Shop(BaseModel):
    shop_id: str
    name: str
    address: str
    area: Optional[str] = None
    city: Optional[str] = None
    contact: Optional[str] = None
    opening_balance: float = 0.0
    balance: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @field_validator("shop_id")
    @classmethod
    def shop_id_not_empty(cls, v: str):
        if not v.strip():
            raise ValueError("shop_id cannot be empty")
        return v.strip()


class Supplier(BaseModel):
    supplier_id: str
    name: str
    address: str
    area: Optional[str] = None
    city: Optional[str] = None
    contact: Optional[str] = None
    opening_balance: float = 0.0
    balance: float = 0.0  # what WE owe the supplier
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @field_validator("supplier_id")
    @classmethod
    def supplier_id_not_empty(cls, v: str):
        if not v.strip():
            raise ValueError("supplier_id cannot be empty")
        return v.strip()


class Item(BaseModel):
    item_id: str
    company_name: Optional[str] = None
    product_name: str
    size: Optional[str] = None
    trade_price: float = 0.0
    company_price: float = 0.0
    retail_price: float
    stock: Optional[int] = 0
    supplier_id: Optional[str] = None  # which supplier this item comes from
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @field_validator("item_id")
    @classmethod
    def item_id_not_empty(cls, v: str):
        if not v.strip():
            raise ValueError("item_id cannot be empty")
        return v.strip()

    @field_validator("retail_price")
    @classmethod
    def price_non_negative(cls, v: float):
        if v < 0:
            raise ValueError("retail_price must be non-negative")
        return v


# ── Bulk Upload ───────────────────────────────────────────────────────────────


def parse_and_validate_file(file: UploadFile, upload_type: str) -> list[dict]:
    filename = file.filename.lower()
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file.file)
        else:
            raise ValueError("Only .csv and .xlsx files are supported")
    except Exception as e:
        raise ValueError(f"File reading error: {str(e)}")

    df.columns = df.columns.str.strip().str.lower()

    model_map = {"shops": Shop, "items": Item, "suppliers": Supplier}
    Model = model_map[upload_type]
    data = []
    error_rows = []

    # ID fields that must be strings even when Excel reads them as numbers
    str_fields = {"item_id", "shop_id", "supplier_id"}

    for idx, row in df.iterrows():
        try:
            row_dict = row.to_dict()
            row_dict = {k: None if pd.isna(v) else v for k, v in row_dict.items()}
            # Coerce numeric ID values to string (e.g. 123 → "123")
            for field in str_fields:
                if field in row_dict and row_dict[field] is not None:
                    row_dict[field] = str(row_dict[field]).strip()
                    # Remove trailing .0 from integers read as floats (e.g. "123.0" → "123")
                    if row_dict[field].endswith(".0"):
                        row_dict[field] = row_dict[field][:-2]
            validated = Model(**row_dict).model_dump()
            # For shops and suppliers: balance starts equal to opening_balance
            if upload_type in ("shops", "suppliers"):
                validated["balance"] = validated.get("opening_balance", 0.0)
            data.append(validated)
        except ValidationError as ve:
            error_rows.append((idx + 2, str(ve)))
        except Exception as e:
            error_rows.append((idx + 2, str(e)))

    if error_rows:
        logger.warning(f"Skipped {len(error_rows)} invalid rows: {error_rows[:3]}...")

    if not data:
        raise ValueError("No valid records found in file")

    return data


@router.post("/upload/{upload_type}")
async def upload_bulk(upload_type: str, file: UploadFile = File(...)):
    if upload_type not in ["shops", "items", "suppliers"]:
        raise HTTPException(400, detail="Type must be 'shops', 'items', or 'suppliers'")

    try:
        records = parse_and_validate_file(file, upload_type)
        collection_map = {
            "shops": shops_collection,
            "items": items_collection,
            "suppliers": suppliers_collection,
        }
        collection = collection_map[upload_type]
        result = collection.insert_many(records, ordered=False)
        inserted_count = len(result.inserted_ids)
        msg = f"Successfully inserted {inserted_count} {upload_type}."
        if inserted_count < len(records):
            msg += f" Skipped {len(records) - inserted_count} duplicates."
        return JSONResponse(
            {
                "status": "success",
                "message": msg,
                "inserted": inserted_count,
                "total_processed": len(records),
            }
        )
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(422, detail=str(e))


# ── List (paginated) ──────────────────────────────────────────────────────────


@router.get("/shops", response_model=dict)
async def list_shops(page: int = Query(1, ge=1), limit: int = Query(25, ge=1)):
    skip = (page - 1) * limit
    total = shops_collection.count_documents({})
    data = list(shops_collection.find({}, {"_id": 0}).skip(skip).limit(limit))
    return {"data": data, "total": total, "page": page, "limit": limit}


@router.get("/suppliers", response_model=dict)
async def list_suppliers(page: int = Query(1, ge=1), limit: int = Query(25, ge=1)):
    skip = (page - 1) * limit
    total = suppliers_collection.count_documents({})
    data = list(suppliers_collection.find({}, {"_id": 0}).skip(skip).limit(limit))
    return {"data": data, "total": total, "page": page, "limit": limit}


@router.get("/items", response_model=dict)
async def list_items(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1),
    supplier_id: Optional[str] = Query(None),
):
    skip = (page - 1) * limit
    filter_q = {}
    if supplier_id:
        filter_q["supplier_id"] = supplier_id
    total = items_collection.count_documents(filter_q)
    data = list(items_collection.find(filter_q, {"_id": 0}).skip(skip).limit(limit))
    return {"data": data, "total": total, "page": page, "limit": limit}


# ── Search (must be before /{id} routes) ─────────────────────────────────────


@router.get("/shops/search", response_model=list)
async def search_shops(q: str = Query("", min_length=1), limit: int = Query(8, le=20)):
    regex = {"$regex": q, "$options": "i"}
    data = list(
        shops_collection.find(
            {"$or": [{"shop_id": regex}, {"name": regex}]},
            {"_id": 0, "shop_id": 1, "name": 1, "balance": 1},
        ).limit(limit)
    )
    return data


@router.get("/suppliers/search", response_model=list)
async def search_suppliers(
    q: str = Query("", min_length=1), limit: int = Query(8, le=20)
):
    regex = {"$regex": q, "$options": "i"}
    data = list(
        suppliers_collection.find(
            {"$or": [{"supplier_id": regex}, {"name": regex}]},
            {"_id": 0, "supplier_id": 1, "name": 1, "balance": 1},
        ).limit(limit)
    )
    return data


@router.get("/items/search", response_model=list)
async def search_items(
    q: str = Query("", min_length=1),
    limit: int = Query(8, le=20),
    supplier_id: Optional[str] = Query(None),
):
    regex = {"$regex": q, "$options": "i"}
    filter_q = {
        "$or": [{"item_id": regex}, {"product_name": regex}, {"company_name": regex}]
    }
    if supplier_id:
        filter_q = {"$and": [{"supplier_id": supplier_id}, {"$or": filter_q["$or"]}]}
    data = list(
        items_collection.find(
            filter_q,
            {
                "_id": 0,
                "item_id": 1,
                "product_name": 1,
                "company_name": 1,
                "size": 1,
                "retail_price": 1,
                "trade_price": 1,
                "stock": 1,
            },
        ).limit(limit)
    )
    return data


# ── Get single ────────────────────────────────────────────────────────────────


@router.get("/shops/{shop_id}", response_model=dict)
async def get_shop(shop_id: str):
    shop = shops_collection.find_one({"shop_id": shop_id}, {"_id": 0})
    if not shop:
        raise HTTPException(404, detail="Shop not found")
    return shop


@router.get("/suppliers/{supplier_id}", response_model=dict)
async def get_supplier(supplier_id: str):
    supplier = suppliers_collection.find_one({"supplier_id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(404, detail="Supplier not found")
    return supplier


@router.get("/items/{item_id}", response_model=dict)
async def get_item(item_id: str):
    item = items_collection.find_one({"item_id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(404, detail="Item not found")
    return item


# ── Add single ────────────────────────────────────────────────────────────────


@router.post("/shops", response_model=dict)
async def add_shop(shop: Shop):
    data = shop.model_dump()
    data["balance"] = data["opening_balance"]
    try:
        shops_collection.insert_one(data)
        data.pop("_id", None)
        return data
    except Exception as e:
        raise HTTPException(400, detail=str(e))


@router.post("/suppliers", response_model=dict)
async def add_supplier(supplier: Supplier):
    data = supplier.model_dump()
    data["balance"] = data["opening_balance"]
    try:
        suppliers_collection.insert_one(data)
        data.pop("_id", None)
        return data
    except Exception as e:
        raise HTTPException(400, detail=str(e))


@router.post("/items", response_model=dict)
async def add_item(item: Item):
    try:
        data = item.model_dump()
        items_collection.insert_one(data)
        data.pop("_id", None)
        return data
    except Exception as e:
        raise HTTPException(400, detail=str(e))


# ── Update single ─────────────────────────────────────────────────────────────


@router.put("/shops/{shop_id}", response_model=dict)
async def update_shop(shop_id: str, shop: Shop):
    if shop.shop_id != shop_id:
        raise HTTPException(400, detail="shop_id mismatch")
    existing = shops_collection.find_one({"shop_id": shop_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, detail="Shop not found")
    data = shop.model_dump()
    data["updated_at"] = datetime.now()
    data["balance"] = existing.get("balance", data["opening_balance"])
    shops_collection.replace_one({"shop_id": shop_id}, data)
    return data


@router.put("/suppliers/{supplier_id}", response_model=dict)
async def update_supplier(supplier_id: str, supplier: Supplier):
    if supplier.supplier_id != supplier_id:
        raise HTTPException(400, detail="supplier_id mismatch")
    existing = suppliers_collection.find_one({"supplier_id": supplier_id}, {"_id": 0})
    if not existing:
        raise HTTPException(404, detail="Supplier not found")
    data = supplier.model_dump()
    data["updated_at"] = datetime.now()
    data["balance"] = existing.get("balance", data["opening_balance"])
    suppliers_collection.replace_one({"supplier_id": supplier_id}, data)
    return data


@router.put("/items/{item_id}", response_model=dict)
async def update_item(item_id: str, item: Item):
    if item.item_id != item_id:
        raise HTTPException(400, detail="item_id mismatch")
    data = item.model_dump()
    data["updated_at"] = datetime.now()
    result = items_collection.replace_one({"item_id": item_id}, data)
    if result.matched_count == 0:
        raise HTTPException(404, detail="Item not found")
    return data
