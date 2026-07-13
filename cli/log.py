from curses import raw
import asyncio
import logging
import sys

import discord
from io import BytesIO
import bot_data

# discord limitation
MAX_MESSAGE_SIZE = 2000
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024 # 10 MiB

async def log(guild):
    log_channel = await guild.fetch_channel(bot_data.CHANNEL_IDS['web-development'])
    assert isinstance(log_channel, discord.TextChannel)

    raw_bytes = sys.stdin.buffer.read()
    data = raw_bytes.decode()

    message = f"```\n{data.replace("`", "\u200b`")}```"

    # choose corresponding message type based on message size
    if len(message) <= MAX_MESSAGE_SIZE:
        await log_channel.send(content=message)
    elif len(data) <= MAX_ATTACHMENT_SIZE:
        await log_channel.send(
            file=discord.File(BytesIO(raw_bytes), filename="output.txt")
        )
    else:
        error = f"Input of size {len(data)} is too large. Expect {MAX_ATTACHMENT_SIZE} characters or less."
        logging.error(error)
