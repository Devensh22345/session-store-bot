import os

# =====================
# BOT CONFIG
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# =====================
# DATABASE
# =====================
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "SESSION_MANAGER")

# =====================
# BASIC CHECK
# =====================
if not BOT_TOKEN or not MONGO_URI or not OWNER_ID:
    raise RuntimeError(
        "Missing required environment variables: "
        "BOT_TOKEN, OWNER_ID, MONGO_URI"
    )
