# (©)CodeXBotz

import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import (
    ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION,
    DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT,
    START_PIC, AUTO_DELETE_TIME, AUTO_DELETE_MSG,
    JOIN_REQUEST_ENABLE, FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL_2
)
from helper_func import subscribed, decode, get_messages, delete_file
from database.database import add_user, del_user, full_userbase, present_user


# ------------------------------------------------------------------
# START COMMAND (SUBSCRIBED USERS)
# ------------------------------------------------------------------
@Bot.on_message(filters.command("start") & filters.private & subscribed)
async def start_command(client: Client, message: Message):

    user_id = message.from_user.id
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass

    text = message.text

    # ---------- DEEP LINK (POST / BATCH) ----------
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except:
            return

        string = await decode(base64_string)
        argument = string.split("-")

        if len(argument) == 3:
            start = int(int(argument[1]) / abs(client.db_channel.id))
            end = int(int(argument[2]) / abs(client.db_channel.id))
            ids = range(start, end + 1) if start <= end else range(start, end - 1, -1)

        elif len(argument) == 2:
            ids = [int(int(argument[1]) / abs(client.db_channel.id))]
        else:
            return

        temp = await message.reply("Please wait...")
        messages = await get_messages(client, ids)
        await temp.delete()

        track_msgs = []

        for msg in messages:
            if CUSTOM_CAPTION and msg.document:
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html,
                    filename=msg.document.file_name
                )
            else:
                caption = "" if not msg.caption else msg.caption.html

            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None

            try:
                copied = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                if AUTO_DELETE_TIME:
                    track_msgs.append(copied)
                await asyncio.sleep(0.5)

            except FloodWait as e:
                await asyncio.sleep(e.value)

        if track_msgs:
            delete_msg = await client.send_message(
                message.chat.id,
                AUTO_DELETE_MSG.format(time=AUTO_DELETE_TIME)
            )
            asyncio.create_task(delete_file(track_msgs, client, delete_msg))

        return

    # ---------- NORMAL /START ----------
    buttons = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("😊 About Me", callback_data="about"),
            InlineKeyboardButton("🔒 Close", callback_data="close")
        ]]
    )

    if START_PIC:
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=buttons
        )
    else:
        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=buttons
        )


# ------------------------------------------------------------------
# START COMMAND (NOT SUBSCRIBED USERS – FORCE SUB)
# ------------------------------------------------------------------
@Bot.on_message(filters.command("start") & filters.private)
async def not_joined(client: Client, message: Message):

    buttons = []
    join_buttons = []
    user_id = message.from_user.id

    # ---------- CHANNEL 1 ----------
    if FORCE_SUB_CHANNEL:
        try:
            await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        except:
            join_buttons.append(
                InlineKeyboardButton("Join Channel 1", url=client.invitelink)
            )

    # ---------- CHANNEL 2 ----------
    if FORCE_SUB_CHANNEL_2:
        try:
            await client.get_chat_member(FORCE_SUB_CHANNEL_2, user_id)
        except:
            join_buttons.append(
                InlineKeyboardButton("Join Channel 2", url=client.invitelink2)
            )

    # JOIN BUTTONS SIDE-BY-SIDE
    if join_buttons:
        buttons.append(join_buttons)

    # ---------- TRY AGAIN (ALWAYS) ----------
    if len(message.command) > 1:
        try_again_url = f"https://t.me/{client.username}?start={message.command[1]}"
    else:
        try_again_url = f"https://t.me/{client.username}?start=retry"

    buttons.append(
        [InlineKeyboardButton("🔄 Try Again", url=try_again_url)]
    )

    await message.reply(
        FORCE_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )


# ------------------------------------------------------------------
# USERS
# ------------------------------------------------------------------
@Bot.on_message(filters.command("users") & filters.private & filters.user(ADMINS))
async def users_cmd(client: Bot, message: Message):
    users = await full_userbase()
    await message.reply(f"{len(users)} users are using this bot")


# ------------------------------------------------------------------
# BROADCAST (FIXED & STABLE)
# ------------------------------------------------------------------
@Bot.on_message(filters.private & filters.command("broadcast") & filters.user(ADMINS))
async def broadcast_cmd(client: Bot, message: Message):

    if not message.reply_to_message:
        warn = await message.reply("<code>Reply to a message to broadcast.</code>")
        await asyncio.sleep(8)
        await warn.delete()
        return

    users = await full_userbase()
    msg = message.reply_to_message

    total = sent = blocked = deleted = failed = 0
    status = await message.reply("<i>📣 Broadcasting… please wait</i>")

    for uid in users:
        try:
            await msg.copy(uid)
            sent += 1

        except FloodWait as e:
            await asyncio.sleep(e.value)
            await msg.copy(uid)
            sent += 1

        except UserIsBlocked:
            await del_user(uid)
            blocked += 1

        except InputUserDeactivated:
            await del_user(uid)
            deleted += 1

        except:
            failed += 1

        total += 1
        await asyncio.sleep(0.1)

    await status.edit(
        f"<b>📊 Broadcast Completed</b>\n\n"
        f"Total: <code>{total}</code>\n"
        f"Sent: <code>{sent}</code>\n"
        f"Blocked: <code>{blocked}</code>\n"
        f"Deleted: <code>{deleted}</code>\n"
        f"Failed: <code>{failed}</code>"
    )
