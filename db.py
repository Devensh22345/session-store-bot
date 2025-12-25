from pymongo import MongoClient
import os
from datetime import datetime

mongo = MongoClient(os.getenv("MONGO_URI"))
db = mongo["SESSION_MANAGER"]
col = db["sessions"]

def save_session(data):
    col.insert_one(data)

def get_all():
    return list(col.find())

def get_one(phone):
    return col.find_one({"phone": phone})

def delete_one(phone):
    col.delete_one({"phone": phone})

def delete_all():
    col.delete_many({})

def update_status(phone, valid):
    col.update_one(
        {"phone": phone},
        {"$set": {"valid": valid, "last_checked": datetime.utcnow()}}
    )
