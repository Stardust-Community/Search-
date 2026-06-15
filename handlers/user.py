# ============================================================
#   ᴜꜱᴇʀ ʜᴀɴᴅʟᴇʀꜱ
# ============================================================

import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from config import REQUEST_CHANNEL
from database import (
    get_post_by_slug, get_post_by_name, search_posts_by_prefix,
    count_posts_by_prefix, register_user, log_request, get_auto_delete
)
from utils import decode_slug, make_deep_link, PAGE_SIZE, paginate, clean_query
from handlers.admin import _auto_delete
from state import get_step


# ══════════════════════════════════════════════════════════════
#   /start  — welcome + deep-link delivery
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, message: Message):
    u = message.from_user
    await register_user(u.id, u.username, u.full_name)

    args = message.command
    if len(args) > 1:
        # Deep-link: deliver stored post
        payload = args[1]
        try:
            slug = decode_slug(payload)
        except Exception:
            await message.reply("「 ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ. 」")
            return
        await _deliver_post(client, message, slug)
        return

    # Normal welcome
    await message.reply(
        "『 ʜᴇʏ ᴛʜᴇʀᴇ! 』\n\n"
        "「 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ɪɴᴅᴇx ʙᴏᴛ. \n"
        "  ᴊᴜꜱᴛ ᴛʏᴘᴇ ᴀ ɴᴀᴍᴇ ᴛᴏ ꜱᴇᴀʀᴄʜ ꜰᴏʀ ᴀ ᴘᴏꜱᴛ,\n"
        "  ᴏʀ ᴜꜱᴇ /search ᴛᴏ ʙʀᴏᴡꜱᴇ ʙʏ ʟᴇᴛᴛᴇʀ. 」\n\n"
        "_ᴄᴏᴍᴍᴀɴᴅꜱ_\n"
        "  » /search `<letter>` — ʙʀᴏᴡꜱᴇ ᴘᴏꜱᴛꜱ\n"
        "  » ᴛʏᴘᴇ ᴀɴʏ ɴᴀᴍᴇ    — ɢᴇᴛ ᴅɪʀᴇᴄᴛ ʀᴇꜱᴜʟᴛ"
    )


# ══════════════════════════════════════════════════════════════
#   /search  <prefix>
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.command("search") & filters.private)
async def cmd_search(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.reply(
            "「 ᴜꜱᴀɢᴇ: `/search A` — ʟɪꜱᴛꜱ ᴀʟʟ ᴘᴏꜱᴛꜱ ꜱᴛᴀʀᴛɪɴɢ ᴡɪᴛʜ ᴀ 」"
        )
        return
    prefix = clean_query(parts[1].strip())
    if not prefix:
        await message.reply(
            "「 ɴᴏᴛʜɪɴɢ ʟᴇꜰᴛ ᴀꜰᴛᴇʀ ᴄʟᴇᴀɴɪɴɢ ᴛʜᴇ ǫᴜᴇʀʏ. ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴀ ɴᴀᴍᴇ ʟɪᴋᴇ `Breaking Bad`. 」"
        )
        return


async def _send_search_page(client, message_or_cq, prefix: str, page: int,
                             send_new: bool = False, edit_msg=None):
    total = await count_posts_by_prefix(prefix)
    info  = paginate(total, page)

    if total == 0:
        text = (
            f"『 ɴᴏ ʀᴇꜱᴜʟᴛꜱ 』\n\n"
            f"「 ɴᴏ ᴘᴏꜱᴛꜱ ꜰᴏᴜɴᴅ ꜱᴛᴀʀᴛɪɴɢ ᴡɪᴛʜ **{prefix.upper()}**. 」\n"
            f"_ʏᴏᴜʀ ǫᴜᴇʀʏ ʜᴀꜱ ʙᴇᴇɴ ʟᴏɢɢᴇᴅ ᴀꜱ ᴀ ʀᴇǫᴜᴇꜱᴛ._"
        )
        uid = (message_or_cq.from_user.id
               if hasattr(message_or_cq, "from_user")
               else message_or_cq.message.from_user.id)
        await log_request(uid, prefix)
        if REQUEST_CHANNEL:
            try:
                await client.send_message(
                    REQUEST_CHANNEL,
                    f"『 ʀᴇǫᴜᴇꜱᴛ 』\n"
                    f"**ᴜꜱᴇʀ**: `{uid}`\n"
                    f"**ǫᴜᴇʀʏ**: `{prefix}`"
                )
            except Exception:
                pass
        if send_new:
            await message_or_cq.reply(text)
        elif edit_msg:
            await edit_msg.edit(text)
        return

    posts  = await search_posts_by_prefix(prefix, info["skip"], info["limit"])
    lines  = []
    for i, p in enumerate(posts, start=info["skip"] + 1):
        lines.append(f"  {i}. {p['name']}")

    text = (
        f"『 ꜱᴇᴀʀᴄʜ: **{prefix.upper()}** 』\n\n"
        + "\n".join(lines)
        + f"\n\n_ᴘᴀɢᴇ {info['page']+1} / {info['pages']}_"
    )

    nav_buttons = []
    if info["page"] > 0:
        nav_buttons.append(InlineKeyboardButton(
            "« ᴘʀᴇᴠ", callback_data=f"srch|{prefix}|{info['page']-1}"
        ))
    if info["page"] < info["pages"] - 1:
        nav_buttons.append(InlineKeyboardButton(
            "ɴᴇxᴛ »", callback_data=f"srch|{prefix}|{info['page']+1}"
        ))

    markup = InlineKeyboardMarkup([nav_buttons]) if nav_buttons else None

    if send_new:
        await message_or_cq.reply(text, reply_markup=markup)
    elif edit_msg:
        await edit_msg.edit(text, reply_markup=markup)


@Client.on_callback_query(filters.regex(r"^srch\|"))
async def cb_search_page(client: Client, cq: CallbackQuery):
    _, prefix, page_str = cq.data.split("|")
    await cq.answer()
    await _send_search_page(client, cq, prefix, int(page_str),
                            send_new=False, edit_msg=cq.message)


# ══════════════════════════════════════════════════════════════
#   Plain text  — name lookup
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.private & filters.text & ~filters.command(
    ["start","search","broadcast","addpost","addadmin","removeadmin",
     "admins","setchannel","autodelete","cancel","stats","deletepost"]
))
async def text_lookup(client: Client, message: Message):
    user_id = message.from_user.id

    # Don't intercept if admin is mid-flow
    if get_step(user_id):
        return

    raw_query = message.text.strip()
    query     = clean_query(raw_query)

    # If the user's input got cleaned (e.g. "Breaking Bad S01" → "Breaking Bad"),
    # we silently use the clean version — no need to confuse them.
    post = await get_post_by_name(query)

    if not post:
        # Log the original raw query so admins see what users actually typed
        await log_request(user_id, raw_query)
        if REQUEST_CHANNEL:
            try:
                await client.send_message(
                    REQUEST_CHANNEL,
                    f"『 ʀᴇǫᴜᴇꜱᴛ 』\n"
                    f"**ᴜꜱᴇʀ**: `{user_id}`\n"
                    f"**ʀᴀᴡ ǫᴜᴇʀʏ**: `{raw_query}`\n"
                    f"**ᴄʟᴇᴀɴᴇᴅ**: `{query}`"
                )
            except Exception:
                pass
        await message.reply(
            f"『 ɴᴏ ʀᴇꜱᴜʟᴛ 』\n\n"
            f"「 ɴᴏ ᴘᴏꜱᴛ ꜰᴏᴜɴᴅ ꜰᴏʀ **{query}**. 」\n"
            "_ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ʟᴏɢɢᴇᴅ._"
        )
        return

    # Send the main-channel version (deep link)
    bot_me = await client.get_me()
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("『 ᴠɪᴇᴡ ᴘᴏꜱᴛ 』", url=post["deep_link"])
    ]])
    sent = await message.reply_photo(
        photo      = post["file_id"],
        caption    = post["caption_html"],
        parse_mode = "html",
        reply_markup = markup,
        quote      = True
    )

    # Auto-delete DM copy
    dm_s, _ = await get_auto_delete()
    if dm_s:
        asyncio.create_task(_auto_delete(client, message.chat.id, sent.id, dm_s))


# ══════════════════════════════════════════════════════════════
#   Deep-link delivery  (called from /start)
# ══════════════════════════════════════════════════════════════

async def _deliver_post(client: Client, message: Message, slug: str):
    post = await get_post_by_slug(slug)
    if not post:
        await message.reply("「 ᴛʜɪꜱ ᴘᴏꜱᴛ ᴄᴏᴜʟᴅ ɴᴏᴛ ʙᴇ ꜰᴏᴜɴᴅ. 」")
        return

    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("『 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ 』", url=post["channel_link"])
    ]])

    sent = await message.reply_photo(
        photo       = post["file_id"],
        caption     = post["caption_html"],
        parse_mode  = "html",
        reply_markup= markup,
        quote       = True
    )

    # Auto-delete DM
    dm_s, _ = await get_auto_delete()
    if dm_s:
        asyncio.create_task(
            _auto_delete(client, message.chat.id, sent.id, dm_s)
        )
