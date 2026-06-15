# ============================================================
#   ᴅᴀᴛᴀʙᴀꜱᴇ — MongoDB helpers
# ============================================================

from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME
import datetime

client = AsyncIOMotorClient(MONGO_URI)
db     = client[DB_NAME]

# ── Collections ──────────────────────────────────────────────
posts_col    = db["posts"]          # stored posts
users_col    = db["users"]          # bot users
settings_col = db["settings"]       # global settings (main channel, auto-delete)
requests_col = db["requests"]       # failed search requests


# ════════════════════════════════════════════════════════════
#   SETTINGS
# ════════════════════════════════════════════════════════════

async def get_setting(key: str):
    doc = await settings_col.find_one({"key": key})
    return doc["value"] if doc else None

async def set_setting(key: str, value):
    await settings_col.update_one(
        {"key": key}, {"$set": {"value": value}}, upsert=True
    )

async def get_main_channel():
    return await get_setting("main_channel")

async def set_main_channel(channel_id: int):
    await set_setting("main_channel", channel_id)

async def get_admins() -> list:
    val = await get_setting("admins")
    return val if val else []

async def add_admin(user_id: int):
    admins = await get_admins()
    if user_id not in admins:
        admins.append(user_id)
        await set_setting("admins", admins)

async def remove_admin(user_id: int):
    admins = await get_admins()
    if user_id in admins:
        admins.remove(user_id)
        await set_setting("admins", admins)

async def get_auto_delete():
    dm = await get_setting("auto_delete_dm")
    ch = await get_setting("auto_delete_ch")
    return (dm or 0, ch or 0)

async def set_auto_delete_dm(seconds: int):
    await set_setting("auto_delete_dm", seconds)

async def set_auto_delete_ch(seconds: int):
    await set_setting("auto_delete_ch", seconds)


# ════════════════════════════════════════════════════════════
#   POSTS
# ════════════════════════════════════════════════════════════

async def save_post(doc: dict):
    """Insert or update a post by its slug key."""
    await posts_col.update_one(
        {"slug": doc["slug"]},
        {"$set": doc},
        upsert=True
    )

async def get_post_by_slug(slug: str):
    return await posts_col.find_one({"slug": slug})

async def get_post_by_name(name: str):
    """Case-insensitive exact match on display name."""
    return await posts_col.find_one(
        {"name": {"$regex": f"^{name}$", "$options": "i"}}
    )

async def search_posts_by_prefix(prefix: str, skip: int = 0, limit: int = 10):
    """Return posts whose name starts with `prefix` (case-insensitive)."""
    cursor = posts_col.find(
        {"name": {"$regex": f"^{prefix}", "$options": "i"}}
    ).sort("name", 1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)

async def count_posts_by_prefix(prefix: str) -> int:
    return await posts_col.count_documents(
        {"name": {"$regex": f"^{prefix}", "$options": "i"}}
    )

async def delete_post_by_slug(slug: str):
    await posts_col.delete_one({"slug": slug})

async def list_all_posts(skip: int = 0, limit: int = 10):
    cursor = posts_col.find().sort("name", 1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)

async def total_posts() -> int:
    return await posts_col.count_documents({})


# ════════════════════════════════════════════════════════════
#   USERS
# ════════════════════════════════════════════════════════════

async def register_user(user_id: int, username: str = None, full_name: str = None):
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id":   user_id,
            "username":  username,
            "full_name": full_name,
            "last_seen": datetime.datetime.utcnow()
        }},
        upsert=True
    )

async def get_all_user_ids() -> list:
    cursor = users_col.find({}, {"user_id": 1})
    docs   = await cursor.to_list(length=None)
    return [d["user_id"] for d in docs]

async def total_users() -> int:
    return await users_col.count_documents({})


# ════════════════════════════════════════════════════════════
#   REQUESTS  (failed searches)
# ════════════════════════════════════════════════════════════

async def log_request(user_id: int, query: str):
    await requests_col.insert_one({
        "user_id":    user_id,
        "query":      query,
        "created_at": datetime.datetime.utcnow()
    })
