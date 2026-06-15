#!/usr/bin/env python3
# ============================================================
#   ɪɴᴅᴇx / ꜰɪʟᴛᴇʀ ʙᴏᴛ  — ᴍᴀɪɴ ᴇɴᴛʀʏ ᴘᴏɪɴᴛ
# ============================================================

from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, MAIN_CHANNEL_SEED
from database import set_main_channel, get_main_channel

# Import handlers so decorators register with the Client class
import handlers.admin   # noqa: F401
import handlers.user    # noqa: F401

app = Client(
    name      = "filter_bot",
    api_id    = API_ID,
    api_hash  = API_HASH,
    bot_token = BOT_TOKEN,
)


async def on_startup():
    # Seed main channel from env if not already set in DB
    existing = await get_main_channel()
    if not existing and MAIN_CHANNEL_SEED:
        await set_main_channel(MAIN_CHANNEL_SEED)
    me = await app.get_me()
    print(f"[ʙᴏᴛ] ᴏɴʟɪɴᴇ ᴀꜱ @{me.username}")


app.add_handler(
    __import__("pyrogram.handlers", fromlist=["RawUpdateHandler"])
    .RawUpdateHandler(lambda *a: None)  # dummy to trigger module loads
)

if __name__ == "__main__":
    app.start()
    import asyncio
    asyncio.get_event_loop().run_until_complete(on_startup())
    print("[ɪɴᴅᴇx ʙᴏᴛ] ʀᴜɴɴɪɴɢ... ᴘʀᴇꜱꜱ ᴄᴛʀʟ+ᴄ ᴛᴏ ꜱᴛᴏᴘ")
    app.idle()
    app.stop()
