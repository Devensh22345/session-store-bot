import base64
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
from datetime import datetime

async def generate_session(api_id, api_hash, phone, otp, password=None):
    app = Client(
        name=f"sess_{phone}",
        api_id=api_id,
        api_hash=api_hash,
        phone_number=phone,
        in_memory=True
    )

    await app.connect()
    try:
        await app.sign_in(phone, otp)
    except SessionPasswordNeeded:
        await app.check_password(password)

    me = await app.get_me()
    session_string = await app.export_session_string()
    session_file = base64.b64encode(app.session.save()).decode()

    await app.disconnect()

    return {
        "name": me.first_name,
        "user_id": me.id,
        "session_string": session_string,
        "session_file": session_file,
        "created_at": datetime.utcnow(),
        "valid": True
    }

async def check_valid(api_id, api_hash, session_string):
    try:
        app = Client(
            "check",
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
            in_memory=True
        )
        await app.connect()
        await app.get_me()
        await app.disconnect()
        return True
    except:
        return False

def decode_file(b64):
    return base64.b64decode(b64)
