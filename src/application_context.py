"""create singleton objects that will be shared with whole application"""

from pymongo import MongoClient


client = MongoClient(
    "mongodb+srv://anshussainmemon_db_user:C0kTYqFuXyagh3ts@cluster0.enzfzcu.mongodb.net/"
)
db = client["distribution_db"]
shops_collection = db["shops"]
items_collection = db["items"]
invoices_collection = db["invoices"]
purchase_invoices_collection = db["purchase_invoices"]
payments_collection = db["payments"]
suppliers_collection = db["suppliers"]
supplier_payments_collection = db["supplier_payments"]

# Unique indexes
shops_collection.create_index("shop_id", unique=True)
items_collection.create_index("item_id", unique=True)
invoices_collection.create_index("invoice_id", unique=True)
purchase_invoices_collection.create_index("invoice_id", unique=True)
payments_collection.create_index("payment_id", unique=True)
suppliers_collection.create_index("supplier_id", unique=True)
supplier_payments_collection.create_index("payment_id", unique=True)
