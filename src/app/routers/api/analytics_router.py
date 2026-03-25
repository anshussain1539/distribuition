from fastapi import APIRouter, Query
from application_context import *
from datetime import datetime, timezone
from typing import Optional


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[],
    responses={404: {"message": "Not found", "code": 404}},
)


@router.get("/summary", response_model=dict)
async def get_summary():
    total_shops = shops_collection.count_documents({})
    total_items = items_collection.count_documents({})
    total_sale_invoices = invoices_collection.count_documents({"status": "completed"})
    total_draft_invoices = invoices_collection.count_documents({"status": "draft"})
    total_purchase_invoices = purchase_invoices_collection.count_documents(
        {"status": "completed"}
    )

    revenue_result = list(
        invoices_collection.aggregate(
            [
                {"$match": {"status": "completed"}},
                {"$group": {"_id": None, "total": {"$sum": "$final_total"}}},
            ]
        )
    )
    total_revenue = revenue_result[0]["total"] if revenue_result else 0.0

    balance_result = list(
        shops_collection.aggregate(
            [{"$group": {"_id": None, "total": {"$sum": "$balance"}}}]
        )
    )
    total_outstanding = balance_result[0]["total"] if balance_result else 0.0

    payment_result = list(
        payments_collection.aggregate(
            [{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
        )
    )
    total_payments = payment_result[0]["total"] if payment_result else 0.0

    recent_invoices = list(
        invoices_collection.find(
            {"status": "completed"},
            {
                "_id": 0,
                "invoice_id": 1,
                "shop_id": 1,
                "final_total": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
        .limit(5)
    )
    top_shops = list(
        shops_collection.find({}, {"_id": 0, "shop_id": 1, "name": 1, "balance": 1})
        .sort("balance", -1)
        .limit(5)
    )

    return {
        "total_shops": total_shops,
        "total_items": total_items,
        "total_sale_invoices": total_sale_invoices,
        "total_draft_invoices": total_draft_invoices,
        "total_purchase_invoices": total_purchase_invoices,
        "total_revenue": round(total_revenue, 2),
        "total_outstanding": round(total_outstanding, 2),
        "total_payments": round(total_payments, 2),
        "recent_invoices": recent_invoices,
        "top_shops_by_balance": top_shops,
    }


@router.get("/range", response_model=dict)
async def get_range_analytics(
    from_date: str = Query(..., description="Start date YYYY-MM-DD"),
    to_date: str = Query(..., description="End date YYYY-MM-DD"),
):
    """Returns sales, purchases, and payments within a date range."""
    try:
        start = datetime.strptime(from_date, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0
        )
        end = datetime.strptime(to_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )
    except ValueError:
        from fastapi import HTTPException

        raise HTTPException(400, detail="Invalid date format. Use YYYY-MM-DD")

    date_filter = {"created_at": {"$gte": start, "$lte": end}}

    # --- Sales ---
    sale_filter = {**date_filter, "status": "completed"}
    sale_count = invoices_collection.count_documents(sale_filter)
    sale_result = list(
        invoices_collection.aggregate(
            [
                {"$match": sale_filter},
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$final_total"},
                        "items_sold": {"$sum": {"$sum": "$items.quantity"}},
                    }
                },
            ]
        )
    )
    sale_total = sale_result[0]["total"] if sale_result else 0.0

    sale_invoices = list(
        invoices_collection.find(
            sale_filter,
            {
                "_id": 0,
                "invoice_id": 1,
                "shop_id": 1,
                "final_total": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
        .limit(100)
    )

    # --- Purchases ---
    purchase_filter = {**date_filter, "status": "completed"}
    purchase_count = purchase_invoices_collection.count_documents(purchase_filter)
    purchase_result = list(
        purchase_invoices_collection.aggregate(
            [
                {"$match": purchase_filter},
                {"$group": {"_id": None, "total": {"$sum": "$total"}}},
            ]
        )
    )
    purchase_total = purchase_result[0]["total"] if purchase_result else 0.0

    purchase_invoices = list(
        purchase_invoices_collection.find(
            purchase_filter,
            {
                "_id": 0,
                "invoice_id": 1,
                "supplier_name": 1,
                "total": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
        .limit(100)
    )

    # --- Payments ---
    payment_count = payments_collection.count_documents(date_filter)
    payment_result = list(
        payments_collection.aggregate(
            [
                {"$match": date_filter},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
            ]
        )
    )
    payment_total = payment_result[0]["total"] if payment_result else 0.0

    payments_list = list(
        payments_collection.find(
            date_filter,
            {
                "_id": 0,
                "payment_id": 1,
                "shop_id": 1,
                "amount": 1,
                "notes": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
        .limit(100)
    )

    return {
        "from_date": from_date,
        "to_date": to_date,
        "sales": {
            "count": sale_count,
            "total": round(sale_total, 2),
            "invoices": sale_invoices,
        },
        "purchases": {
            "count": purchase_count,
            "total": round(purchase_total, 2),
            "invoices": purchase_invoices,
        },
        "payments": {
            "count": payment_count,
            "total": round(payment_total, 2),
            "records": payments_list,
        },
        "net": round(sale_total - purchase_total, 2),
    }
