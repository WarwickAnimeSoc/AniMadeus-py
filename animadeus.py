import bot_data
import config
import discord
from discord.ext.commands import Bot
import asyncio
import cli.set_member as set_member
import cli.log as log
from off_topic import OffTopicCog
import argparse
import daemon

async def async_main():
    parser = argparse.ArgumentParser()
    
    commands = parser.add_subparsers(dest="command", required=True)

    set_member_parser = commands.add_parser(
        "set-member",
        help="add the member role to the provided discord user"
    )
    set_member_parser.add_argument(
        "user_id",
        type=int,
        help="the discord id of the target user"
    )

    log_parser = commands.add_parser(
        "log",
        help="log the provided stdin into the web development channel"
    )

    daemon_parser = commands.add_parser(
        "daemon",
        help="start the original long running discord bot"
    )

    args = parser.parse_args()

    # Intents
    intents = discord.Intents.default()
    intents.members = True
    intents.messages = True
    intents.message_content = True

    # Bot instance
    bot = Bot(command_prefix='!', description='The Warwick Anime & Manga Society Discord Bot.', intents=intents)

    await bot.login(config.bot_token)

    try:

        # get discord server
        guild = await bot.fetch_guild(bot_data.GUILD_ID)
        assert guild is not None, "server must exist"

        # run the selected command

        if args.command == "set-member":
            await set_member.set_member(guild, args.user_id)

        if args.command == "log":
            await log.log(guild)

        if args.command == "daemon":
            await daemon.setup_daemon(bot)
            await bot.connect()

    finally:
        await bot.close()

    
def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()

