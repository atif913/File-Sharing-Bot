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


# -------------------- START (SUBSCRIBED) --------------------
@Bot.on_message(filters.command('start') & filters.private & subscribed, group=0)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass

    markup = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("😊 About Me", callback_data="about"),
            InlineKeyboardButton("🔒 Close", callback_data="close")
        ]]
    )

    if START_PIC:
        await message.reply_photo(
            START_PIC,
            START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=markup
        )
    else:
        await message.reply_text(
            START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=markup
        )


# -------------------- START (NOT SUBSCRIBED) --------------------
@Bot.on_message(filters.command('start') & filters.private & ~subscribed, group=0)
async def not_joined(client: Client, message: Message):

    user_id = message.from_user.id
    join_buttons = []

    if FORCE_SUB_CHANNEL:
        try:
            m = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
            if m.status not in ("member", "administrator", "owner"):
                raise Exception
        except:
            join_buttons.append(
                InlineKeyboardButton("Join Channel 1", url=client.invitelink)
            )

    if FORCE_SUB_CHANNEL_2:
        try:
            m = await client.get_chat_member(FORCE_SUB_CHANNEL_2, user_id)
            if m.status not in ("member", "administrator", "owner"):
                raise Exception
        except:
            join_buttons.append(
                InlineKeyboardButton("Join Channel 2", url=client.invitelink2)
            )

    if not join_buttons:
        return

    payload = message.command[1] if len(message.command) > 1 else "retry"
    try_again = f"https://t.me/{client.username}?start={payload}"

    buttons = [
        join_buttons,
        [InlineKeyboardButton("🔄 Try Again", url=try_again)]
    ]

    await message.reply_text(
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


# -------------------- BROADCAST --------------------
@Bot.on_message(
    filters.private & filters.command('broadcast') & filters.user(ADMINS),
    group=1
)
async def send_text(client: Bot, message: Message):

    if not message.reply_to_message:
        msg = await message.reply("<code>Reply to a message to broadcast.</code>")
        await asyncio.sleep(5)
        await msg.delete()
        return

    users = await full_userbase()
    total = success = 0

    for user in users:
        try:
            await message.reply_to_message.copy(user)
            success += 1
        except:
            pass
        total += 1

    await message.reply(f"Broadcast done: {success}/{total}")
