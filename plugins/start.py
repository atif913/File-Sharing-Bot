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
@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):

    if await client.check_force_sub(message) != True:
        return

    user_id = message.from_user.id
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass

    text = message.text
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

        temp_msg = await message.reply("Please wait...")
        messages = await get_messages(client, ids)
        await temp_msg.delete()

        track_msgs = []

        for msg in messages:
            caption = (
                CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html,
                    filename=msg.document.file_name
                ) if CUSTOM_CAPTION and msg.document else
                "" if not msg.caption else msg.caption.html
            )

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

    # NORMAL START
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
@Bot.on_message(filters.command("start") & filters.private)
async def force_sub_handler(client: Client, message: Message):

    user_id = message.from_user.id
    join_buttons = []

    # CHANNEL 1
    if FORCE_SUB_CHANNEL:
        try:
            member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
            if member.status in ("left", "kicked"):
                raise Exception
        except Exception:
            join_buttons.append(
                InlineKeyboardButton("📢 Join Channel 1", url=client.invitelink)
            )

    # CHANNEL 2
    if FORCE_SUB_CHANNEL_2:
        try:
            member = await client.get_chat_member(FORCE_SUB_CHANNEL_2, user_id)
            if member.status in ("left", "kicked"):
                raise Exception
        except Exception:
            join_buttons.append(
                InlineKeyboardButton("📢 Join Channel 2", url=client.invitelink2)
            )

    if join_buttons:
        buttons = [
            join_buttons,
            [InlineKeyboardButton("🔄 Try Again", callback_data="force_retry")]
        ]

        await message.reply_text(
            FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=f"@{message.from_user.username}" if message.from_user.username else None,
                mention=message.from_user.mention,
                id=user_id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True,
            disable_web_page_preview=True
        )
        return

    await start_command(client, message)


# -------------------- FORCE SUB RETRY CALLBACK --------------------
@Bot.on_callback_query(filters.regex("^force_retry$"))
async def force_retry_callback(client: Client, query):

    user_id = query.from_user.id
    join_buttons = []

    # CHANNEL 1
    if FORCE_SUB_CHANNEL:
        try:
            member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
            if member.status in ("left", "kicked"):
                raise Exception
        except Exception:
            join_buttons.append(
                InlineKeyboardButton("📢 Join Channel 1", url=client.invitelink)
            )

    # CHANNEL 2
    if FORCE_SUB_CHANNEL_2:
        try:
            member = await client.get_chat_member(FORCE_SUB_CHANNEL_2, user_id)
            if member.status in ("left", "kicked"):
                raise Exception
        except Exception:
            join_buttons.append(
                InlineKeyboardButton("📢 Join Channel 2", url=client.invitelink2)
            )

    if join_buttons:
        await query.message.edit_reply_markup(
            InlineKeyboardMarkup([
                join_buttons,
                [InlineKeyboardButton("🔄 Try Again", callback_data="force_retry")]
            ])
        )
        await query.answer("Join required channels first", show_alert=False)
        return

    await query.message.delete()
    fake_msg = query.message
    fake_msg.text = "/start"
    await start_command(client, fake_msg)


# -------------------- USERS --------------------
@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    users = await full_userbase()
    await message.reply(f"{len(users)} users are using this bot")


# -------------------- BROADCAST --------------------
@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):

    if not message.reply_to_message:
        msg = await message.reply("<code>Reply to a message to broadcast.</code>")
        await asyncio.sleep(8)
        await msg.delete()
        return

    query = await full_userbase()
    broadcast_msg = message.reply_to_message

    total = successful = blocked = deleted = unsuccessful = 0
    pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")

    for chat_id in query:
        try:
            await broadcast_msg.copy(chat_id)
            successful += 1
        except FloodWait as e:
            await asyncio.sleep(e.x)
            await broadcast_msg.copy(chat_id)
            successful += 1
        except UserIsBlocked:
            await del_user(chat_id)
            blocked += 1
        except InputUserDeactivated:
            await del_user(chat_id)
            deleted += 1
        except:
            unsuccessful += 1
        total += 1

    await pls_wait.edit(
        f"<b><u>Broadcast Completed</u>\n\n"
        f"Total Users: <code>{total}</code>\n"
        f"Successful: <code>{successful}</code>\n"
        f"Blocked: <code>{blocked}</code>\n"
        f"Deleted: <code>{deleted}</code>\n"
        f"Unsuccessful: <code>{unsuccessful}</code></b>"
    )
