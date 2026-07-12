import config
import discord
import bot_data
import logging
import mysql.connector

# TODO: not production ready
async def link_if_member(guild: discord.Guild, web_dev: discord.TextChannel, user_id: int) -> None:
    """
    give the provided discord user the member role,
    if corresponding discord id is in server database.
    """

    member_role = guild.get_role(bot_data.ROLE_IDS['member'])
    assert member_role is not None

    target_member = guild.get_member(user_id)
    if target_member is None:
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
        await web_dev.send("animadeus failed to connect to database")

    cursor = conn.cursor()

    query = ('SELECT discord_id FROM members_member'
             ' WHERE members_member.discord_id = %s LIMIT 1;')

    cursor.execute(query, (user_id,))

    # the existence of the user id in the database is proof that the account is a member account.
    is_member = cursor.fetchone() is not None

    # TODO: need escaping
    if is_member:
        await target_member.add_roles(member_role)
        await web_dev.send(f"added member role to {target_member.name}")


