# ============================================================
#   ᴘᴇʀᴍꜱ — permission decorators
# ============================================================

from functools import wraps
from pyrogram.types import Message
from config import OWNER_ID
from database import get_admins


async def is_privileged(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    admins = await get_admins()
    return user_id in admins


def owner_only(func):
    """Allow only the bot owner."""
    @wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        if message.from_user.id != OWNER_ID:
            await message.reply(
                "『 ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ 』\n"
                "「 ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪꜱ ʀᴇꜱᴇʀᴠᴇᴅ ғᴏʀ ᴛʜᴇ ᴏᴡɴᴇʀ ᴏɴʟʏ. 」",
                quote=True
            )
            return
        return await func(client, message, *args, **kwargs)
    return wrapper


def admin_only(func):
    """Allow owner + admins."""
    @wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        if not await is_privileged(message.from_user.id):
            await message.reply(
                "『 ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ 』\n"
                "「 ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪꜱ ᴏɴʟʏ ᴀᴠᴀɪʟᴀʙʟᴇ ᴛᴏ ᴀᴅᴍɪɴꜱ. 」",
                quote=True
            )
            return
        return await func(client, message, *args, **kwargs)
    return wrapper
