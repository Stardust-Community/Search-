# ============================================================
#   ғɪʟᴛᴇʀ ʙᴏᴛ — ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

# ── Core Telegram credentials ────────────────────────────────
API_ID              = int(os.getenv("API_ID", "0"))
API_HASH            = os.getenv("API_HASH", "")
BOT_TOKEN           = os.getenv("BOT_TOKEN", "")
OWNER_ID            = int(os.getenv("OWNER_ID", "0"))

# ── MongoDB ──────────────────────────────────────────────────
MONGO_URI           = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME             = os.getenv("DB_NAME", "filterbot")

# ── Channels (set via commands or env) ───────────────────────
# POST_STORE_CHANNEL  : private channel where full posts are saved
# REQUEST_CHANNEL     : channel where failed search names are logged
POST_STORE_CHANNEL  = int(os.getenv("POST_STORE_CHANNEL", "0"))
REQUEST_CHANNEL     = int(os.getenv("REQUEST_CHANNEL", "0"))

# MAIN_CHANNEL is set via /setchannel command and stored in DB.
# The env value below is only a fallback seed.
MAIN_CHANNEL_SEED   = int(os.getenv("MAIN_CHANNEL_SEED", "0"))

# ── Auto-delete defaults (seconds, 0 = disabled) ────────────
DEFAULT_DM_DELETE   = int(os.getenv("DEFAULT_DM_DELETE", "0"))
DEFAULT_CH_DELETE   = int(os.getenv("DEFAULT_CH_DELETE", "0"))
