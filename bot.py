from aiohttp import web
from plugins import web_server

import pyromod.listen
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from config import (
    API_HASH,
    APP_ID,
    LOGGER,
    TG_BOT_TOKEN,
    TG_BOT_WORKERS,
    CHANNEL_ID,
    PORT,
    ADMINS,
)

# Dynamic Fsub variables
FSUB_ENABLED = True  # Force subscription enabled by default
FSUB_CHANNEL = None  # Dynamic channel ID (set via commands)


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def setup_fsub(self):
        """Setup force subscription logic asynchronously."""
        global FSUB_CHANNEL

        if FSUB_ENABLED and FSUB_CHANNEL:
            try:
                # Check if the channel mode is direct or request
                mode = await db.get_fsub_mode(FSUB_CHANNEL)  # Fetch mode from the database

                if mode == "direct":
                    # Generate or fetch the direct invite link
                    link = (await self.get_chat(FSUB_CHANNEL)).invite_link
                    if not link:
                        await self.export_chat_invite_link(FSUB_CHANNEL)
                        link = (await self.get_chat(FSUB_CHANNEL)).invite_link
                    self.invitelink = link

                elif mode == "request":
                    # Generate a join request invite link
                    link = (await self.create_chat_invite_link(
                        chat_id=FSUB_CHANNEL,
                        creates_join_request=True
                    )).invite_link
                    self.invitelink = link

                else:
                    raise ValueError(f"Invalid FSUB mode for channel {FSUB_CHANNEL}. Expected 'direct' or 'request'.")

            except Exception as e:
                self.LOGGER(__name__).warning(f"Error during FSUB setup: {e}")
                self.LOGGER(__name__).warning("Failed to export invite link for FSUB channel!")
                self.LOGGER(__name__).warning(f"Check FSUB_CHANNEL ({FSUB_CHANNEL}) and ensure the bot is admin with invite permissions.")
                sys.exit()

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        # Setup FSUB logic
        await self.setup_fsub()

        # Validate DB channel access
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(f"Ensure bot is admin in DB channel with CHANNEL_ID ({CHANNEL_ID}).")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Bot Running..!\n\nCreated by \nhttps://t.me/rohit_1888")
        print("Welcome to Bot Modified by Rohit")
        self.username = usr_bot_me.username

        # Web server setup
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")