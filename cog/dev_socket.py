import logging
from io import BytesIO
import discord
from curses import raw
import asyncio
from discord.ext import commands
import config
import bot_data
import os

# discord limitation
MAX_MESSAGE_SIZE = 2000
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024 # 10 MiB

class DevSocketCog(commands.Cog):
    """
    Cog for creating a unix socket to development channel,
    for arbitrary command outputting.
    """

    bot: commands.Bot
    server: asyncio.Server | None

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.server = None

    async def cog_load(self) -> None:
        if os.path.exists(config.dev_socket):
            os.unlink(config.dev_socket)

        self.server = await asyncio.start_unix_server(
            self.handle_input,
            path=config.dev_socket
        )
        
        self.task = asyncio.create_task(self.server.serve_forever())

    async def cog_unload(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        if self.task:
            self.task.cancel()

        if os.path.exists(config.dev_socket):
            os.unlink(config.dev_socket)

    async def handle_input(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:

        # get input data from socket
        raw_bytes = await reader.read()
        data = raw_bytes.decode()

        guild = self.bot.get_guild(bot_data.GUILD_ID)
        assert guild is not None

        channel = guild.get_channel(bot_data.CHANNEL_IDS['web-development'])
        assert isinstance(channel, discord.TextChannel)

        # choose corresponding message type based on message size
        if len(data) <= MAX_MESSAGE_SIZE:
            await channel.send(content=data)
        elif len(data) <= MAX_ATTACHMENT_SIZE:
            await channel.send(
                file=discord.File(BytesIO(raw_bytes), filename="output.txt")
            )
        else:
            error = f"Input of size {len(data)} is too large. Expect {MAX_ATTACHMENT_SIZE} characters or less."
            logging.error(error)
            writer.write((error + "\n").encode())
        
        writer.close()
        await writer.wait_closed()


