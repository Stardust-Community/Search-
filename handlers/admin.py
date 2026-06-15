# ============================================================
#   ᴀᴅᴍɪɴ ʜᴀɴᴅʟᴇʀꜱ
# ============================================================

import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton
)
from config import OWNER_ID, POST_STORE_CHANNEL, REQUEST_CHANNEL
from database import (
    save_post, get_post_by_slug, set_main_channel, get_main_channel,
    add_admin, remove_admin, get_admins, set_auto_delete_dm,
    set_auto_delete_ch, get_auto_delete, get_setting, set_setting
)
from utils import (
    make_slug, encode_slug, make_deep_link, entities_to_html, parse_time, fmt_time
)
from state import set_state, get_step, get_data, update_data, clear_state, STEPS
from perms import owner_only, admin_only


# ══════════════════════════════════════════════════════════════
#   /addpost  — start the post-creation wizard
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.command("addpost") & filters.private)
@admin_only
async def cmd_addpost(client: Client, message: Message):
    set_state(message.from_user.id, STEPS["AWAIT_POST_NAME"])
    await message.reply(
        "『 ɴᴇᴡ ᴘᴏꜱᴛ ᴄʀᴇᴀᴛɪᴏɴ 』\n\n"
        "「 ꜱᴛᴇᴘ 1 / 3 」\n"
        "ꜱᴇɴᴅ ᴍᴇ ᴛʜᴇ *ɴᴀᴍᴇ* ᴏꜰ ᴛʜᴇ ᴘᴏꜱᴛ.\n\n"
        "_ᴛɪᴘ: ᴋᴇᴇᴘ ɪᴛ ꜱʜᴏʀᴛ ᴀɴᴅ ꜱᴇᴀʀᴄʜᴀʙʟᴇ._",
        quote=True
    )


# ══════════════════════════════════════════════════════════════
#   /cancel
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(client: Client, message: Message):
    clear_state(message.from_user.id)
    await message.reply(
        "『 ᴄᴀɴᴄᴇʟʟᴇᴅ 』\n"
        "「 ᴀʟʟ ᴘᴇɴᴅɪɴɢ ᴀᴄᴛɪᴏɴꜱ ʜᴀᴠᴇ ʙᴇᴇɴ ᴄʟᴇᴀʀᴇᴅ. 」"
    )


# ══════════════════════════════════════════════════════════════
#   STATE-DRIVEN HANDLER  (private messages, non-command)
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.private & ~filters.command(
    ["start","search","broadcast","addpost","addadmin","removeadmin",
     "admins","setchannel","autodelete","cancel","stats","deletepost"]
))
async def state_handler(client: Client, message: Message):
    user_id = message.from_user.id
    step    = get_step(user_id)

    # ── Step 1: receive post name ─────────────────────────────
    if step == STEPS["AWAIT_POST_NAME"]:
        name = message.text.strip() if message.text else None
        if not name:
            await message.reply("「 ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴀ ᴛᴇxᴛ ɴᴀᴍᴇ ᴏɴʟʏ. 」")
            return
        slug = make_slug(name)
        update_data(user_id, name=name, slug=slug)
        set_state(user_id, STEPS["AWAIT_POST_IMAGE"], name=name, slug=slug)
        await message.reply(
            f"『 ɴᴀᴍᴇ ꜱᴀᴠᴇᴅ 』— `{name}`\n\n"
            "「 ꜱᴛᴇᴘ 2 / 3 」\n"
            "ɴᴏᴡ ꜱᴇɴᴅ ᴍᴇ ᴛʜᴇ *ɪᴍᴀɢᴇ ᴡɪᴛʜ ᴄᴀᴘᴛɪᴏɴ*.\n"
            "_ᴛʜᴇ ᴄᴀᴘᴛɪᴏɴ ᴍᴀʏ ɪɴᴄʟᴜᴅᴇ ʙᴏʟᴅ, ɪᴛᴀʟɪᴄ, ǫᴜᴏᴛᴇꜱ ᴇᴛᴄ. — ɪ ᴡɪʟʟ ᴘʀᴇꜱᴇʀᴠᴇ ᴛʜᴇᴍ._",
            quote=True
        )
        return

    # ── Step 2: receive image + caption ──────────────────────
    if step == STEPS["AWAIT_POST_IMAGE"]:
        if not message.photo:
            await message.reply("「 ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴀɴ *ɪᴍᴀɢᴇ* ᴡɪᴛʜ ᴀ ᴄᴀᴘᴛɪᴏɴ. 」")
            return

        data      = get_data(user_id)
        caption   = message.caption or ""
        entities  = message.caption_entities or []
        html_cap  = entities_to_html(caption, entities)
        file_id   = message.photo.file_id

        update_data(user_id,
                    caption=caption,
                    caption_html=html_cap,
                    file_id=file_id,
                    entities=[(e.type, e.offset, e.length,
                               getattr(e,"url",""),
                               getattr(e,"language","")) for e in entities])
        set_state(user_id, STEPS["AWAIT_POST_LINK"],
                  **get_data(user_id))
        await message.reply(
            "『 ɪᴍᴀɢᴇ ꜱᴀᴠᴇᴅ 』\n\n"
            "「 ꜱᴛᴇᴘ 3 / 3 」\n"
            "ɴᴏᴡ ꜱᴇɴᴅ ᴍᴇ ᴛʜᴇ *ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ* ᴛʜᴀᴛ ᴡɪʟʟ ʙᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴏɴ ᴛʜᴇ ᴘᴏꜱᴛ.\n"
            "_ᴇxᴀᴍᴘʟᴇ: `https://t.me/yourchannel`_",
            quote=True
        )
        return

    # ── Step 3: receive channel link → publish ────────────────
    if step == STEPS["AWAIT_POST_LINK"]:
        link = message.text.strip() if message.text else None
        if not link or not link.startswith("http"):
            await message.reply("「 ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ʜᴛᴛᴘ ʟɪɴᴋ. 」")
            return

        data        = get_data(user_id)
        name        = data["name"]
        slug        = data["slug"]
        file_id     = data["file_id"]
        caption_html = data["caption_html"]
        clear_state(user_id)

        # ── 1. Save full post (with channel link) to store channel ──
        bot_me     = await client.get_me()
        deep_link  = make_deep_link(bot_me.username, slug)

        store_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("『 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ 』", url=link)
        ]])

        store_msg = await client.send_photo(
            chat_id   = POST_STORE_CHANNEL,
            photo     = file_id,
            caption   = caption_html,
            parse_mode= "html",
            reply_markup = store_markup
        )

        # ── 2. Post to main channel with deep-link button ───────
        main_channel = await get_main_channel()
        if not main_channel:
            await message.reply(
                "『 ᴡᴀʀɴɪɴɢ 』\n"
                "「 ɴᴏ ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ ꜱᴇᴛ ʏᴇᴛ. ᴜꜱᴇ /setchannel ᴛᴏ ꜱᴇᴛ ᴏɴᴇ ᴀɴᴅ ʀᴇᴘᴏꜱᴛ. 」"
            )
            # Save post without main_msg_id
            await save_post({
                "slug":           slug,
                "name":           name,
                "file_id":        file_id,
                "caption_html":   caption_html,
                "channel_link":   link,
                "store_msg_id":   store_msg.id,
                "main_msg_id":    None,
                "deep_link":      deep_link,
            })
            return

        main_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("『 ɢᴇᴛ ᴘᴏꜱᴛ 』", url=deep_link)
        ]])

        main_msg = await client.send_photo(
            chat_id   = main_channel,
            photo     = file_id,
            caption   = caption_html,
            parse_mode= "html",
            reply_markup = main_markup
        )

        # ── 3. Auto-delete main channel post if configured ─────
        _, ch_secs = await get_auto_delete()
        if ch_secs:
            asyncio.create_task(_auto_delete(client, main_channel, main_msg.id, ch_secs))

        # ── 4. Persist to MongoDB ───────────────────────────────
        await save_post({
            "slug":           slug,
            "name":           name,
            "file_id":        file_id,
            "caption_html":   caption_html,
            "channel_link":   link,
            "store_msg_id":   store_msg.id,
            "main_msg_id":    main_msg.id,
            "deep_link":      deep_link,
        })

        await message.reply(
            f"『 ᴘᴏꜱᴛ ᴘᴜʙʟɪꜱʜᴇᴅ 』\n\n"
            f"**ɴᴀᴍᴇ** — `{name}`\n"
            f"**ʟɪɴᴋ** — {deep_link}\n\n"
            "「 ᴛʜᴇ ᴘᴏꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ꜱᴇɴᴛ ᴛᴏ ᴛʜᴇ ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ. 」",
            quote=True
        )
        return

    # ── Auto-delete DM time ───────────────────────────────────
    if step == STEPS["AWAIT_AD_DM_TIME"]:
        secs = parse_time(message.text.strip() if message.text else "")
        if secs is None:
            await message.reply(
                "「 ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ. ᴇxᴀᴍᴘʟᴇꜱ: `5m` `2h` `1d` `0` ᴛᴏ ᴅɪꜱᴀʙʟᴇ. 」"
            )
            return
        await set_auto_delete_dm(secs)
        clear_state(user_id)
        await message.reply(
            f"『 ᴅᴍ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ 』 ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ **{fmt_time(secs)}**."
        )
        return

    if step == STEPS["AWAIT_AD_CH_TIME"]:
        secs = parse_time(message.text.strip() if message.text else "")
        if secs is None:
            await message.reply(
                "「 ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ. ᴇxᴀᴍᴘʟᴇꜱ: `5m` `2h` `5d` `0` ᴛᴏ ᴅɪꜱᴀʙʟᴇ. 」"
            )
            return
        await set_auto_delete_ch(secs)
        clear_state(user_id)
        await message.reply(
            f"『 ᴄʜᴀɴɴᴇʟ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ 』 ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ **{fmt_time(secs)}**."
        )
        return


# ══════════════════════════════════════════════════════════════
#   /setchannel  <channel_id or @username>
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.command("setchannel") & filters.private)
@owner_only
async def cmd_setchannel(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "「 ᴜꜱᴀɢᴇ: `/setchannel @username` ᴏʀ `/setchannel -100xxxxxxxxxx` 」"
        )
        return
    arg = parts[1].strip()
    try:
        chat = await client.get_chat(arg)
        await set_main_channel(chat.id)
        await message.reply(
            f"『 ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ ꜱᴇᴛ 』\n"
            f"「 **{chat.title}** (`{chat.id}`) ᴡɪʟʟ ɴᴏᴡ ʀᴇᴄᴇɪᴠᴇ ᴘᴏꜱᴛꜱ. 」"
        )
    except Exception as e:
        await message.reply(f"『 ᴇʀʀᴏʀ 』 — `{e}`")


# ══════════════════════════════════════════════════════════════
#   /addadmin  /removeadmin  /admins
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.command("addadmin") & filters.private)
@owner_only
async def cmd_addadmin(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("「 ᴜꜱᴀɢᴇ: `/addadmin <user_id>` 」")
        return
    try:
        uid = int(parts[1].strip())
        await add_admin(uid)
        await message.reply(f"『 ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ 』 — `{uid}`")
    except ValueError:
        await message.reply("「 ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴜꜱᴇʀ ɪᴅ. 」")


@Client.on_message(filters.command("removeadmin") & filters.private)
@owner_only
async def cmd_removeadmin(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("「 ᴜꜱᴀɢᴇ: `/removeadmin <user_id>` 」")
        return
    try:
        uid = int(parts[1].strip())
        await remove_admin(uid)
        await message.reply(f"『 ᴀᴅᴍɪɴ ʀᴇᴍᴏᴠᴇᴅ 』 — `{uid}`")
    except ValueError:
        await message.reply("「 ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴜꜱᴇʀ ɪᴅ. 」")


@Client.on_message(filters.command("admins") & filters.private)
@owner_only
async def cmd_admins(client: Client, message: Message):
    admins = await get_admins()
    if not admins:
        await message.reply("「 ɴᴏ ᴀᴅᴍɪɴꜱ ꜱᴇᴛ ʏᴇᴛ. 」")
        return
    lines = "\n".join(f"  » `{a}`" for a in admins)
    await message.reply(f"『 ᴀᴅᴍɪɴ ʟɪꜱᴛ 』\n{lines}")


# ══════════════════════════════════════════════════════════════
#   /autodelete
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.command("autodelete") & filters.private)
@admin_only
async def cmd_autodelete(client: Client, message: Message):
    dm_s, ch_s = await get_auto_delete()
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"『 ᴅᴍ 』 ― {fmt_time(dm_s)}", callback_data="ad_dm")],
        [InlineKeyboardButton(
            f"『 ᴄʜᴀɴɴᴇʟ 』 ― {fmt_time(ch_s)}", callback_data="ad_ch")],
    ])
    await message.reply(
        "『 ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ꜱᴇᴛᴛɪɴɢꜱ 』\n\n"
        "「 ᴄʜᴏᴏꜱᴇ ᴡʜɪᴄʜ ᴛɪᴍᴇʀ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴꜰɪɢᴜʀᴇ. 」",
        reply_markup=markup, quote=True
    )


@Client.on_callback_query(filters.regex("^ad_(dm|ch)$"))
async def cb_autodelete(client, cq):
    kind = cq.data.split("_")[1]
    user_id = cq.from_user.id
    from perms import is_privileged
    if not await is_privileged(user_id):
        await cq.answer("ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ.", show_alert=True)
        return

    if kind == "dm":
        from state import set_state, STEPS
        set_state(user_id, STEPS["AWAIT_AD_DM_TIME"])
        await cq.message.reply(
            "「 ꜱᴇɴᴅ ᴛʜᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ ꜰᴏʀ **ᴅᴍ** ᴍᴇꜱꜱᴀɢᴇꜱ.\n"
            "ᴇxᴀᴍᴘʟᴇꜱ: `5m` · `2h` · `1d` · `0` ᴛᴏ ᴅɪꜱᴀʙʟᴇ 」"
        )
    else:
        from state import set_state, STEPS
        set_state(user_id, STEPS["AWAIT_AD_CH_TIME"])
        await cq.message.reply(
            "「 ꜱᴇɴᴅ ᴛʜᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ ꜰᴏʀ **ᴄʜᴀɴɴᴇʟ** ᴘᴏꜱᴛꜱ.\n"
            "ᴇxᴀᴍᴘʟᴇꜱ: `5d` · `2h` · `0` ᴛᴏ ᴅɪꜱᴀʙʟᴇ 」"
        )
    await cq.answer()


# ══════════════════════════════════════════════════════════════
#   /deletepost  <name>
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.command("deletepost") & filters.private)
@admin_only
async def cmd_deletepost(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("「 ᴜꜱᴀɢᴇ: `/deletepost <post name>` 」")
        return
    name = parts[1].strip()
    from database import get_post_by_name, delete_post_by_slug
    post = await get_post_by_name(name)
    if not post:
        await message.reply(f"「 ɴᴏ ᴘᴏꜱᴛ ꜰᴏᴜɴᴅ ɴᴀᴍᴇᴅ **{name}**. 」")
        return
    await delete_post_by_slug(post["slug"])
    await message.reply(
        f"『 ᴘᴏꜱᴛ ᴅᴇʟᴇᴛᴇᴅ 』 — **{name}**\n"
        "「 ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀꜱᴇ. 」"
    )


# ══════════════════════════════════════════════════════════════
#   /stats
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.command("stats") & filters.private)
@owner_only
async def cmd_stats(client: Client, message: Message):
    from database import total_posts, total_users
    p = await total_posts()
    u = await total_users()
    dm_s, ch_s = await get_auto_delete()
    ch = await get_main_channel()
    await message.reply(
        "『 ʙᴏᴛ ꜱᴛᴀᴛꜱ 』\n\n"
        f"  » ᴘᴏꜱᴛꜱ     — **{p}**\n"
        f"  » ᴜꜱᴇʀꜱ     — **{u}**\n"
        f"  » ᴄʜᴀɴɴᴇʟ   — `{ch}`\n"
        f"  » ᴅᴍ ᴀᴜᴛᴏᴅᴇʟ — **{fmt_time(dm_s)}**\n"
        f"  » ᴄʜ ᴀᴜᴛᴏᴅᴇʟ — **{fmt_time(ch_s)}**"
    )


# ══════════════════════════════════════════════════════════════
#   /broadcast  (reply to a message)
# ══════════════════════════════════════════════════════════════

@Client.on_message(filters.command("broadcast") & filters.private)
@owner_only
async def cmd_broadcast(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply("「 ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪᴛ. 」")
        return
    users    = await get_all_user_ids()
    sent, fail = 0, 0
    prog_msg = await message.reply(f"「 ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ ᴛᴏ {len(users)} ᴜꜱᴇʀꜱ... 」")
    for uid in users:
        try:
            await message.reply_to_message.copy(uid)
            sent += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await prog_msg.edit(
        f"『 ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇ 』\n\n"
        f"  » ꜱᴇɴᴛ    — **{sent}**\n"
        f"  » ꜰᴀɪʟᴇᴅ  — **{fail}**"
    )


# ══════════════════════════════════════════════════════════════
#   HELPER  — auto-delete coroutine
# ══════════════════════════════════════════════════════════════

async def _auto_delete(client: Client, chat_id, msg_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, msg_id)
    except Exception:
        pass
