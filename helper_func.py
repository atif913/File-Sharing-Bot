# (©)CodeXBotz

import base64
import re
import asyncio
from pyrogram.errors import FloodWait
from config import (
    FORCE_SUB_CHANNEL,
    FORCE_SUB_CHANNEL_2,
    ADMINS,
    AUTO_DELETE_TIME,
    AUTO_DEL_SUCCESS_MSG
)


# -------------------------------------------------
# FORCE SUB CHECK (MANUAL)
# -------------------------------------------------
async def check_subscribed(client, message):
    user_id = message.from_user.id

    if user_id in ADMINS:
        return True

    try:
        if FORCE_SUB_CHANNEL:
            await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)

        if FORCE_SUB_CHANNEL_2:
            await client.get_chat_member(FORCE_SUB_CHANNEL_2, user_id)

        return True
    except:
        return False


# -------------------------------------------------
# BASE64 UTILS
# -------------------------------------------------
async def encode(string):
    return base64.urlsafe_b64encode(string.encode()).decode().strip("=")


async def decode(base64_string):
    base64_string += "=" * (-len(base64_string) % 4)
    return base64.urlsafe_b64decode(base64_string.encode()).decode()


# -------------------------------------------------
# DB MESSAGE HELPERS
# -------------------------------------------------
async def get_messages(client, message_ids):
    messages = []
    index = 0

    while index < len(message_ids):
        batch = message_ids[index:index + 200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=batch
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=batch
            )
        except:
            msgs = []

        messages.extend(msgs)
        index += len(batch)

    return messages


async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        return 0

    if message.text:
        match = re.match(r"https://t.me/(?:c/)?(.+?)/(\d+)", message.text)
        if not match:
            return 0

        channel, msg_id = match.groups()
        msg_id = int(msg_id)

        if channel.isdigit():
            return msg_id if f"-100{channel}" == str(client.db_channel.id) else 0

        return msg_id if channel == client.db_channel.username else 0

    return 0


# -------------------------------------------------
# AUTO DELETE
# -------------------------------------------------
async def delete_file(messages, client, process):
    await asyncio.sleep(AUTO_DELETE_TIME)

    for msg in messages:
        try:
            await client.delete_messages(msg.chat.id, msg.id)
        except:
            pass

    await process.edit_text(AUTO_DEL_SUCCESS_MSG)


def get_readable_time(seconds: int) -> str:
    count = 0
    time_list = []
    suffix = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(f"{int(result)}{suffix[count-1]}")
        seconds = int(remainder)

    return ":".join(reversed(time_list))
