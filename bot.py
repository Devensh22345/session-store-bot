import os, base64
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from db import *
from session_utils import *
from config import BOT_TOKEN, OWNER_ID, MONGO_URI


load_dotenv()


BOT = Client(
    "session_manager_bot",
    api_id=1,
    api_hash="1",
    bot_token=os.getenv("BOT_TOKEN")
)

OWNER = int(os.getenv("OWNER_ID"))
TEMP = {}

def panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Session", callback_data="add")],
        [InlineKeyboardButton("📋 List Sessions", callback_data="list")],
        [InlineKeyboardButton("✅ Check Validity", callback_data="check")],
        [InlineKeyboardButton("📤 Get Session", callback_data="get")],
        [InlineKeyboardButton("❌ Remove Session", callback_data="remove")],
        [InlineKeyboardButton("🧹 Remove All", callback_data="clear")]
    ])

@BOT.on_message(filters.command("start") & filters.user(OWNER))
async def start(_, m):
    await m.reply("🔐 **Pyrogram Session Manager**", reply_markup=panel())

@BOT.on_callback_query(filters.user(OWNER))
async def cb(_, q):
    uid = q.from_user.id

    if q.data == "add":
        TEMP[uid] = {}
        await q.message.reply("Send API_ID")

    elif q.data == "list":
        data = get_all()
        if not data:
            return await q.message.reply("No sessions")
        msg = ""
        for d in data:
            msg += f"{d['name']} | `{d['phone']}` | ✅ {d['valid']}\n"
        await q.message.reply(msg)

    elif q.data == "check":
        for d in get_all():
            ok = await check_valid(
                d["api_id"], d["api_hash"], d["session_string"]
            )
            update_status(d["phone"], ok)
        await q.message.reply("✅ Validity updated")

    elif q.data == "get":
        await q.message.reply("Send phone number")

    elif q.data == "remove":
        await q.message.reply("Send phone number to delete")

    elif q.data == "clear":
        delete_all()
        await q.message.reply("All sessions removed")

@BOT.on_message(filters.user(OWNER) & filters.text)
async def steps(_, m):
    uid = m.from_user.id
    t = m.text

    if uid not in TEMP:
        s = get_one(t)
        if not s:
            delete_one(t)
            return await m.reply("❌ Session deleted")

        await m.reply(f"🔑 Session String:\n`{s['session_string']}`")

        file = decode_file(s["session_file"])
        fname = f"{t}.session"
        with open(fname, "wb") as f:
            f.write(file)
        await m.reply_document(fname)
        return

    d = TEMP[uid]

    if "api_id" not in d:
        d["api_id"] = int(t)
        return await m.reply("Send API_HASH")

    if "api_hash" not in d:
        d["api_hash"] = t
        return await m.reply("Send phone number")

    if "phone" not in d:
        d["phone"] = t
        app = Client("otp", api_id=d["api_id"], api_hash=d["api_hash"])
        await app.connect()
        await app.send_code(t)
        await app.disconnect()
        return await m.reply("Send OTP")

    if "otp" not in d:
        info = await generate_session(
            d["api_id"], d["api_hash"], d["phone"], t
        )
        save_session({
            "api_id": d["api_id"],
            "api_hash": d["api_hash"],
            "phone": d["phone"],
            **info
        })
        TEMP.pop(uid)
        await m.reply(f"✅ Session added for {info['name']}")

BOT.run()
