import os

# =====================
# BOT CONFIG
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN" ,"7611358375:AAET1Zs1DSNhuSeXhJfDvc6GFhOZn5YgC5Q")
OWNER_ID = int(os.getenv("OWNER_ID", "6872968794"))

# =====================
# DATABASE
# =====================
MONGO_URI = os.getenv("MONGO_URI",  "mongodb+srv://5:5@cluster0.otqyz3n.mongodb.net/?appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "SESSION_MANAGER")

# =====================
# BASIC CHECK
# =====================
if not BOT_TOKEN or not MONGO_URI or not OWNER_ID:
    raise RuntimeError(
        "Missing required environment variables: "
        "BOT_TOKEN, OWNER_ID, MONGO_URI"
    )
