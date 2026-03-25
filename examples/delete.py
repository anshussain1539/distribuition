"""
Bulk delete script for MongoDB collections.
Deletes ALL documents from ALL collections.
⚠️ Use ONLY in development or when you are 100% sure.
"""

import os
from pymongo import MongoClient


# =========================
# CONFIG
# =========================
MONGO_URI = "mongodb+srv://anshussainmemon_db_user:C0kTYqFuXyagh3ts@cluster0.enzfzcu.mongodb.net/"
DB_NAME = "distribution_db"

# Safety flag (change to "YES" to allow deletion)
ALLOW_BULK_DELETE = "YES"


# =========================
# DB CONNECTION
# =========================
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

COLLECTIONS = [
    "shops",
    "items",
    "invoices",
    "purchase_invoices",
    "suppliers",
    "payments",
    "supplier_payments",
]


# =========================
# BULK DELETE FUNCTION
# =========================
def bulk_delete_all():
    if ALLOW_BULK_DELETE != "YES":
        raise RuntimeError(
            "Bulk delete is disabled. Set ALLOW_BULK_DELETE=YES to proceed."
        )

    results = {}
    for name in COLLECTIONS:
        result = db[name].delete_many({})
        results[name] = result.deleted_count

    return results


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL data from ALL MongoDB collections.")
    print("Collections:", ", ".join(COLLECTIONS))
    confirm = input("Type YES to confirm: ").strip()
    if confirm != "YES":
        print("Aborted.")
        exit(0)

    result = bulk_delete_all()

    print("\n✅ Bulk delete completed")
    for col, count in result.items():
        print(f"  {col}: {count} deleted")

    print("\n📊 Remaining counts (should all be 0):")
    for name in COLLECTIONS:
        print(f"  {name}: {db[name].count_documents({})}")
