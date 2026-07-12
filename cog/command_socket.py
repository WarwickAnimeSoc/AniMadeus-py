import logging
from io import BytesIO
import discord
import asyncio
from discord.ext import commands
import config
import bot_data
import os
from actions.link_if_member import link_if_member

# discord limitation
MAX_MESSAGE_SIZE = 2000
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024 # 10 MiB

class CommandSocketCog(commands.Cog):
    """
    Cog for creating a unix socket to development channel,
    for arbitrary command outputting.
    """

    bot: commands.Bot
    server: asyncio.Server | None
    guild: discord.Guild
    web_dev: discord.TextChannel

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.server = None

    async def cog_load(self) -> None:
        if os.path.exists(config.command_socket):
            os.unlink(config.command_socket)
    
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        guild = self.bot.get_guild(bot_data.GUILD_ID)
        assert guild is not None
        self.guild = guild

        web_dev = self.guild.get_channel(bot_data.CHANNEL_IDS['web-development'])
        assert isinstance(web_dev, discord.TextChannel)
        self.web_dev = web_dev

        self.server = await asyncio.start_unix_server(
            self.handle_command,
            path=config.command_socket
        )

        self.task = asyncio.create_task(self.server.serve_forever())

    async def cog_unload(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        if self.task:
            self.task.cancel()

        if os.path.exists(config.command_socket):
            os.unlink(config.command_socket)

    async def handle_command(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:

        # get input data from socket
        raw_bytes = await reader.read()
        commands = raw_bytes.decode()

        for command in commands.splitlines():
            command = command.strip().split()

            try:

                if len(command) == 0:
                    continue

                # memberfy <discord id>
                if command[0] == 'memberfy':
                    await link_if_member(self.guild, self.web_dev, int(command[1]))
                    continue

                raise Exception(f"unknown command: {" ".join(command)}")

            except Exception as e:
                logging.error("Failed to process command: %s", e)
                await self.web_dev.send("exception occured when processing animadeus command in command socket, see animadeus server logs")
        
        writer.close()
        await writer.wait_closed()


