#!/usr/bin/env python3
# ============================================================
#   ɪɴᴅᴇx / ꜰɪʟᴛᴇʀ ʙᴏᴛ  — ᴍᴀɪɴ ᴇɴᴛʀʏ ᴘᴏɪɴᴛ
#   Render-compatible:
#     • aiohttp health-check server on $PORT  (required by Render)
#     • Pyrogram session stored on persistent disk (/app/session)
#       so it survives redeploys without re-auth
# ============================================================

import asyncio
import os
from pathlib import Path

from aiohttp import web
from pyrogram import Client

from config import API_ID, API_HASH, BOT_TOKEN, MAIN_CHANNEL_SEED
from database import set_main_channel, get_main_channel

# Import handler modules — their @Client.on_* decorators self-register
import handlers.admin  # noqa: F401
import handlers.user   # noqa: F401


# ── Session path ─────────────────────────────────────────────
# On Render the persistent disk is mounted at /app/session (see render.yaml).
# Locally the session file sits in the current working directory.
_RENDER_SESSION_DIR = Path("/app/session")
SESSION_NAME = (
    str(_RENDER_SESSION_DIR / "filter_bot")
    if _RENDER_SESSION_DIR.exists()
    else "filter_bot"
)

# ── Pyrogram client ──────────────────────────────────────────
app = Client(
    name      = SESSION_NAME,
    api_id    = API_ID,
    api_hash  = API_HASH,
    bot_token = BOT_TOKEN,
)


# ── Health-check server ───────────────────────────────────────
# Render requires a process to bind a TCP port and respond to HTTP.
# We serve a single GET / endpoint; anything 2xx keeps the service alive.
PORT = int(os.getenv("PORT", "8080"))

async def _health(_request):
    return web.Response(text="『 ꜰɪʟᴛᴇʀ ʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ 』")

async def _start_health_server():
    web_app = web.Application()
    web_app.router.add_get("/", _health)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"[ʜᴇᴀʟᴛʜ] HTTP server listening on port {PORT}")


# ── Startup tasks ────────────────────────────────────────────
async def _on_startup():
    # Seed main channel from env if nothing is stored in DB yet
    existing = await get_main_channel()
    if not existing and MAIN_CHANNEL_SEED:
        await set_main_channel(MAIN_CHANNEL_SEED)
        print(f"[ꜱᴇᴛᴜᴘ] main channel seeded from env: {MAIN_CHANNEL_SEED}")

    me = await app.get_me()
    print(f"[ʙᴏᴛ] online as @{me.username}  (id: {me.id})")
    print(f"[ꜱᴇꜱꜱɪᴏɴ] stored at: {SESSION_NAME}.session")


# ── Main coroutine ───────────────────────────────────────────
async def main():
    # 1. Bind the health-check port FIRST so Render marks the
    #    deploy as healthy before the bot connects to Telegram.
    await _start_health_server()

    # 2. Start Pyrogram (connects to Telegram, registers handlers)
    await app.start()
    await _on_startup()

    print("[ɪɴᴅᴇx ʙᴏᴛ] running — press Ctrl+C to stop")

    # 3. Block forever (aiohttp + Pyrogram both run on this event loop)
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[ʙᴏᴛ] shutting down...")
