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
    FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL_2
)
from helper_func import check_subscribed, decode, get_messages, delete_file
from database.database import add_user, del_user, full_userbase, present_user


@Bot.on_message(filters.command("start") & filters.private)
async def start_router(client: Client, message: Message):

    user_id = message.from_user.id

    # ---------------- FORCE SUB ----------------
    if not await check_subscribed(client, message):

        join_buttons = []

        if FORCE_SUB_CHANNEL:
            try:
                await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
            except:
                join_buttons.append(
                    InlineKeyboardButton("Join Channel 1", url=client.invitelink)
                )

        if FORCE_SUB_CHANNEL_2:
            try:
                await client.get_chat_member(FORCE_SUB_CHANNEL_2, user_id)
            except:
                join_buttons.append(
                    InlineKeyboardButton("Join Channel 2", url=client.invitelink2)
                )

        buttons = []
        if join_buttons:
            buttons.append(join_buttons)

        payload = message.command[1] if len(message.command) > 1 else "retry"
        retry_url = f"https://t.me/{client.username}?start={payload}"

        buttons.append([InlineKeyboardButton("🔄 Try Again", url=retry_url)])

        await message.reply(
            FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=user_id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
        return

    # ---------------- USER OK ----------------
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass

    if len(message.command) > 1:
        try:
            string = await decode(message.command[1])
        except:
            return

        args = string.split("-")

        if len(args) == 3:
            start = int(int(args[1]) / abs(client.db_channel.id))
            end = int(int(args[2]) / abs(client.db_channel.id))
            ids = range(start, end + 1) if start <= end else range(start, end - 1, -1)
        elif len(args) == 2:
            ids = [int(int(args[1]) / abs(client.db_channel.id))]
        else:
            return

        temp = await message.reply("Please wait...")
        messages = await get_messages(client, ids)
        await temp.delete()

        track = []

        for msg in messages:
            caption = (
                CUSTOM_CAPTION.format(
                    previouscaption=msg.caption.html if msg.caption else "",
                    filename=msg.document.file_name
                )
                if CUSTOM_CAPTION and msg.document
                else msg.caption.html if msg.caption else ""
            )

            copied = await msg.copy(
                chat_id=message.chat.id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=msg.reply_markup if DISABLE_CHANNEL_BUTTON else None,
                protect_content=PROTECT_CONTENT
            )

            if AUTO_DELETE_TIME:
                track.append(copied)

            await asyncio.sleep(0.3)

        if track:
            msg = await client.send_message(
                message.chat.id,
                AUTO_DELETE_MSG.format(time=AUTO_DELETE_TIME)
            )
            asyncio.create_task(delete_file(track, client, msg))

        return

    # ---------------- NORMAL START ----------------
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("😊 About Me", callback_data="about"),
        InlineKeyboardButton("🔒 Close", callback_data="close")
    ]])

    if START_PIC:
        await message.reply_photo(
            START_PIC,
            START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=user_id
            ),
            reply_markup=buttons
        )
    else:
        await message.reply_text(
            START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=user_id
            ),
            reply_markup=buttons
        )
