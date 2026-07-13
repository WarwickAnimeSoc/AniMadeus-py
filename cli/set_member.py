from discord.utils import escape_mentions

import config
import discord
import bot_data
import logging
import mysql.connector
import argparse


# Used to assign users the Member role.
#
# The member role is assigned to users that have linked their website (animesoc.co.uk) account with their discord.
# The current website API is barebones and lacks any form of authentication. Discord tag to member's website accounts
# could be considered sensitive by some. So to avoid needing to implement authentication on the API the bot connects
# to the MYSQL server that contains the site's database to find the discord tag.
#
# For this command to work the bot must be running on the same machine as the website's database.
async def set_member(guild: discord.Guild, user_id: int) -> None:
    """
    give the provided discord user the member role,
    if corresponding discord id is in server database.
    """

    log_channel = await guild.fetch_channel(bot_data.CHANNEL_IDS['web-development'])
    assert isinstance(log_channel, discord.TextChannel)

    member_role = await guild.fetch_role(bot_data.ROLE_IDS['member'])

    try:
        target_member = await guild.fetch_member(user_id)
    except discord.NotFound:
        logging.warning(f"tried to set member role to unknown user id: {user_id}, expected if added on website before joining discord server.")
        return

    try:
        conn = mysql.connector.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password)
    except mysql.connector.Error:
        await log_channel.send("animadeus failed to connect to database")

    cursor = conn.cursor()

    query = ('SELECT discord_id FROM members_member'
             ' WHERE members_member.discord_id = %s LIMIT 1;')

    cursor.execute(query, (user_id,))

    # the existence of the user id in the database is proof that the account is a member account.
    is_member = cursor.fetchone() is not None

    if is_member:
        await target_member.add_roles(member_role)
        await log_channel.send(
            f"added member role to {target_member.mention}",
            allowed_mentions=discord.AllowedMentions.none()
        )


