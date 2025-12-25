import os
import base64
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import SessionPasswordNeeded
from db import *
from session_utils import *
from config import BOT_TOKEN, OWNER_ID

# ------------------- Encode / Decode Helpers -------------------
def encode_file(file_path: str) -> str:
    """Encode a local file to base64 string for storage."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def decode_file(data: str) -> bytes:
    """Decode base64 string back to bytes for file download."""
    return base64.b64decode(data)

# ------------------- Bot Initialization -------------------
BOT = Client(
    "session_manager_bot",
    api_id="22207976",
    api_hash="5c0ad7c48a86afac87630ba28b42560d",
    bot_token=BOT_TOKEN
)

TEMP = {}  # Temporary per-user storage during login flow

# ------------------- Inline Panel -------------------
def panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Session", callback_data="add")],
        [InlineKeyboardButton("📋 List Sessions", callback_data="list")],
        [InlineKeyboardButton("✅ Check Validity", callback_data="check")],
        [InlineKeyboardButton("📤 Get Session", callback_data="get")],
        [InlineKeyboardButton("❌ Remove Session", callback_data="remove")],
        [InlineKeyboardButton("🧹 Remove All", callback_data="clear")]
    ])

# ------------------- /start Command -------------------
@BOT.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start(_, m):
    await m.reply("🔐 **Pyrogram Session Manager**", reply_markup=panel())

# ------------------- Callback Queries -------------------
@BOT.on_callback_query(filters.user(OWNER_ID))
async def cb(_, q):
    uid = q.from_user.id

    if q.data == "add":
        TEMP[uid] = {}
        await q.message.reply("Send **API_ID**")

    elif q.data == "list":
        data = get_all()
        if not data:
            return await q.message.reply("❌ No sessions found")
        msg = ""
        for d in data:
            msg += f"👤 {d['name']} | `{d['phone']}` | {'✅' if d['valid'] else '❌'}\n"
        await q.message.reply(msg)

    elif q.data == "check":
        for d in get_all():
            ok = await check_valid(d["api_id"], d["api_hash"], d["session_string"])
            update_status(d["phone"], ok)
        await q.message.reply("✅ Validity updated")

    elif q.data == "get":
        await q.message.reply("Send phone number to retrieve session")

    elif q.data == "remove":
        await q.message.reply("Send phone number to delete session")

    elif q.data == "clear":
        delete_all()
        await q.message.reply("🧹 All sessions removed")

# ------------------- Text Messages (Add / Get / Delete Sessions) -------------------
@BOT.on_message(filters.user(OWNER_ID) & filters.text)
async def steps(_, m):
    uid = m.from_user.id
    text = m.text.strip()

    # ----- GET / DELETE SESSIONS -----
    if uid not in TEMP:
        s = get_one(text)
        if s:
            # Send session string & session file
            await m.reply(f"🔑 **Session String:**\n`{s['session_string']}`")
            file = decode_file(s["session_file"])
            fname = f"{text}.session"
            with open(fname, "wb") as f:
                f.write(file)
            await m.reply_document(fname)
            os.remove(fname)
        else:
            delete_one(text)
            await m.reply("❌ Session deleted")
        return

    # ----- ADD SESSION FLOW -----
    d = TEMP[uid]

    if "api_id" not in d:
        d["api_id"] = int(text)
        return await m.reply("Send **API_HASH**")

    if "api_hash" not in d:
        d["api_hash"] = text
        return await m.reply("Send **Phone Number** (with country code)")

    if "phone" not in d:
        d["phone"] = text
        d["client"] = Client(
            name="login",
            api_id=d["api_id"],
            api_hash=d["api_hash"],
            in_memory=True
        )
        await d["client"].connect()

        # ✅ Send login code and save phone_code_hash
        sent = await d["client"].send_code(d["phone"])
        d["phone_code_hash"] = sent.phone_code_hash
        return await m.reply("Send **OTP** you received on Telegram")

    if "otp" not in d:
        try:
            # ✅ Sign in using OTP and phone_code_hash
            await d["client"].sign_in(
                phone_number=d["phone"],
                phone_code=text,
                phone_code_hash=d["phone_code_hash"]
            )
        except SessionPasswordNeeded:
            d["otp"] = text
            return await m.reply("🔐 **2FA Enabled**\nSend your **Telegram password**")
        return await finalize_session(uid, m)

    if "password" not in d:
        # ✅ Handle 2FA password
        await d["client"].check_password(text)
        return await finalize_session(uid, m)

# ------------------- Finalize & Save Session -------------------
async def finalize_session(uid, m):
    d = TEMP[uid]
    client = d["client"]

    me = await client.get_me()
    session_string = await client.export_session_string()
    session_file = encode_file(client.storage.database)

    save_session({
        "api_id": d["api_id"],
        "api_hash": d["api_hash"],
        "phone": d["phone"],
        "name": me.first_name,
        "session_string": session_string,
        "session_file": session_file,
        "valid": True
    })

    await client.disconnect()
    TEMP.pop(uid)
    await m.reply(f"✅ **Session Added:** {me.first_name}")

# ------------------- Run Bot -------------------
BOT.run()
