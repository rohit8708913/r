#(©)Codexbotz

import base64
import re
import asyncio
import logging 
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNEL, ADMINS, AUTO_DELETE_TIME, AUTO_DEL_SUCCESS_MSG
from pyrogram.errors import FloodWait
from config import FSUB_ENABLED, FSUB_CHANNEL  # Ensure FSUB_ENABLED is imported from config
from pyrogram.errors import UserNotParticipant, RPCError


async def is_subscribed(filter, client, update):
    global FSUB_ENABLED, FSUB_CHANNEL, ADMINS

    # If Fsub is disabled, allow all users
    if not FSUB_ENABLED:
        return True

    user_id = update.from_user.id

    # Admins bypass the Fsub check
    if user_id in ADMINS:
        return True

    try:
        # Check if the user is a member of the FSUB_CHANNEL
        member = await client.get_chat_member(chat_id=FSUB_CHANNEL, user_id=user_id)

        # Return True if the user is a member, admin, or owner
        return member.status in [
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        ]

    except UserNotParticipant:
        # Handle the case where the user is not part of the channel
        print(f"User {user_id} is not a participant of {FSUB_CHANNEL}.")
        return False

    except RPCError as e:
        # Handle other Telegram API exceptions
        print(f"RPC error in is_subscribed filter: {e}")
        return False

    except Exception as e:
        # Catch any unexpected errors
        print(f"Error in is_subscribed filter: {e}")
        return False

# Register the filter
subscribed = filters.create(is_subscribed)

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string


async def decode(base64_string: str) -> str:
    try:
        # Strip any padding characters and normalize the string length
        base64_string = base64_string.strip("=")
        padded_string = base64_string + "=" * (-len(base64_string) % 4)
        
        # Decode the base64 string
        base64_bytes = padded_string.encode("ascii")
        string_bytes = base64.urlsafe_b64decode(base64_bytes)
        string = string_bytes.decode("ascii")

        return string

    except (base64.binascii.Error, ValueError) as e:
        # Handle invalid base64 strings
        print(f"Error decoding base64 string: {e}")
        return None

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern,message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

async def delete_file(messages, client, process):
    await asyncio.sleep(AUTO_DELETE_TIME)
    for msg in messages:
        try:
            await client.delete_messages(chat_id=msg.chat.id, message_ids=[msg.id])
        except Exception as e:
            await asyncio.sleep(e.x)
            print(f"The attempt to delete the media {msg.id} was unsuccessful: {e}")

    await process.edit_text(AUTO_DEL_SUCCESS_MSG)

