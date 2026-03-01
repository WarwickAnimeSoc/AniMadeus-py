# AniMadeus main file
import subprocess
import random
import sqlite3
from datetime import datetime

import discord
from discord.ext import commands
import mysql.connector
import requests

import bot_data
import config
from off_topic import OffTopicCog


# Intents
intents = discord.Intents.default()
intents.members = True
intents.messages = True

# Bot instance
bot = commands.Bot(command_prefix='!', description='The Warwick Anime & Manga Society Discord Bot.', intents=intents)


# Startup event.
#
# Currently only sets the status.
@bot.event
async def on_ready():
    await bot.change_presence(activity=config.status_activity)


# Bot-commands check.
#
# Checks if a command was run in the bot-commands channel.
def bot_commands_channel_check(ctx):
    return ctx.message.channel.id == bot_data.CHANNEL_IDS['bot-commands']


# Web-development check.
#
# Checks if a command was run in the web-development channel.
def web_development_channel_check(ctx):
    return ctx.message.channel.id == bot_data.CHANNEL_IDS['web-development']


# Karaoke-discussion check.
#
# Checks if a command was run in the karaoke-discussion channel.
def karaoke_discussion_channel_check(ctx):
    return ctx.message.channel.id == bot_data.CHANNEL_IDS['karaoke-discussion']


# DM check.
#
# Checks if a command was run in DMs with the bot.
def dm_channel_check(ctx):
    return isinstance(ctx.message.channel, discord.DMChannel)


# Event listener for member joins.
#
# Used to welcome new users.
@bot.listen()
async def on_member_join(member):
    guild = bot.get_guild(bot_data.GUILD_ID)
    newcomers_channel = guild.get_channel(bot_data.CHANNEL_IDS['newcomers'])
    welcome_channel = guild.get_channel(bot_data.CHANNEL_IDS['welcome-and-links'])
    rules_channel = guild.get_channel(bot_data.CHANNEL_IDS['rules'])
    role_channel = guild.get_channel(bot_data.CHANNEL_IDS['role-assign'])
    welcome_string = ('Welcome to the Warwick Anime and Manga Society Discord server, {0}!'
                      ' Please see {1} and {2} for information about the society and this server.'
                      ' To gain access to the rest of the server please react to the message in {3}!')
    await newcomers_channel.send(
        welcome_string.format(member.mention, welcome_channel.mention, rules_channel.mention, role_channel.mention))


# Event listener for reaction adds.
#
# Used for the role assign system.
@bot.listen()
async def on_raw_reaction_add(payload):
    if payload.message_id == bot_data.MESSAGE_IDS['role_assign_message']:
        await on_general_role_assignment_add(payload)    

    # if the message moves, this needs to be updated.
    if payload.message_id == bot_data.MESSAGE_IDS['manga_club_role_assign_message']:
        await on_manga_club_role_add(payload)


# Event listener for reaction adds.
#
# Used for the role assign system.
@bot.listen()
async def on_raw_reaction_remove(payload):    
    if payload.message_id == bot_data.MESSAGE_IDS['role_assign_message']:
        await on_general_role_assignment_remove(payload)

    # if the message moves, this needs to be updated.
    if payload.message_id == bot_data.MESSAGE_IDS['manga_club_role_assign_message']:
        await on_manga_club_role_remove(payload)


# Event listener for reaction adds.
#
# Used for the role assign system in #role-assign.
async def on_general_role_assignment_add(payload):
    try:
        # If we start using custom emoji this will need editing
        role_id = bot_data.EMOJI_TO_ROLE_MAPPINGS[str(payload.emoji)]
    except KeyError:
        return

    role = bot.get_guild(bot_data.GUILD_ID).get_role(role_id)
    if role is None:
        return

    try:
        await payload.member.add_roles(role)
    except discord.HTTPException:
        pass


# Event listener for reaction removals.
#
# Used for the role assign system in #role-assign.
async def on_general_role_assignment_remove(payload):    
    try:
        # If we start using custom emoji this will need editing
        role_id = bot_data.EMOJI_TO_ROLE_MAPPINGS[str(payload.emoji)]
    except KeyError:
        return

    role = bot.get_guild(bot_data.GUILD_ID).get_role(role_id)
    if role is None:
        return

    member = bot.get_guild(bot_data.GUILD_ID).get_member(payload.user_id)
    if member is None:
        return

    try:
        await member.remove_roles(role)
    except discord.HTTPException:
        pass


# Event listener for reaction adds.
#
# NOTE: temporary solution, may remove at some point?
# Used for the role assign system in #role-assign.
async def on_manga_club_role_add(payload):
    try:
        role_id = bot_data.ROLE_IDS['manga']
    except KeyError:
        return

    role = bot.get_guild(bot_data.GUILD_ID).get_role(role_id)
    if role is None:
        return

    try:
        await payload.member.add_roles(role)
    except discord.HTTPException:
        pass


# Event listener for reaction removals.
#
# NOTE: temporary solution, may remove at some point?
# Used for the role assign system in #role-assign.
async def on_manga_club_role_remove(payload):    
    try:
        role_id = bot_data.ROLE_IDS['manga']
    except KeyError:
        return

    guild = bot.get_guild(bot_data.GUILD_ID)

    role = guild.get_role(role_id)
    if role is None:
        return

    member = guild.get_member(payload.user_id)
    if member is None:
        return

    channel = guild.get_channel(bot_data.CHANNEL_IDS['announcements'])
    if channel is None:
        return

    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.HTTPException:
        return

    reacted = False
    for reaction in message.reactions:
        async for user in reaction.users():
            if user.id == member.id:
                reacted = True
                break
        if reacted:
            break

    if not reacted:
        try:
            await member.remove_roles(role)
        except discord.HTTPException:
            pass


# Member command.
#
# Used to assign users the Member role.
#
# The member role is assigned to users that have linked their website (animesoc.co.uk) account with their discord.
# The current website API is barebones and lacks any form of authentication. Discord tag to member's website accounts
# could be considered sensitive by some. So to avoid needing to implement authentication on the API the bot connects
# to the MYSQL server that contains the site's database to find the discord tag.
#
# For this command to work the bot must be running on the same machine as the website's database.
@bot.command(pass_context=True)
@commands.check(dm_channel_check)
async def member(ctx, member_id: int):
    if len(str(member_id)) != 7:
        return await ctx.message.channel.send('{0} - Your university id should be 7 digits long.'.format(
            ctx.message.author.mention))

    try:
        conn = mysql.connector.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password)
    except mysql.connector.Error:
        await ctx.message.channel.send(
            '{0} - An error occurred when running this command, please wait for the webmaster to fix it.'.format(
                ctx.message.author.mention))
        webmaster = ctx.message.guild.get_role(bot_data.ROLE_IDS['webmaster'])
        web_development_channel = bot.get_guild(bot_data.GUILD_ID).get_channel(bot_data.CHANNEL_IDS['web-development'])
        return await web_development_channel.send(
            '{0} - There was an SQL connection error when executing the member command.'.format(webmaster.mention))

    cursor = conn.cursor()

    query = ('SELECT discord_tag FROM members_member'
             ' INNER JOIN auth_user ON auth_user.id = members_member.user_id'
             ' WHERE auth_user.username = %s;')

    cursor.execute(query, (member_id,))

    tag_matched = False
    result_found = False
    for (discord_tag,) in cursor:
        result_found = True
        tag_matched = discord_tag == '{0}'.format(ctx.message.author.name)

    conn.close()

    if tag_matched:
        member_role = bot.get_guild(bot_data.GUILD_ID).get_role(bot_data.ROLE_IDS['member'])
        member_server = bot.get_guild(bot_data.GUILD_ID).get_member(ctx.message.author.id)
        await member_server.add_roles(member_role)
        return await ctx.message.channel.send('{0} - Member role added.'.format(ctx.message.author.mention))
    elif result_found:
        return await ctx.message.channel.send('{0} - The discord tag for this user does not match yours.'.format(
            ctx.message.author.mention))
    else:
        return await ctx.message.channel.send('{0} - No member with this ID was found.'.format(
            ctx.message.author.mention))


# Member command error handler.
@member.error
async def on_member_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        return await ctx.message.channel.send(
            '{0} - You are using this command incorrectly. The correct usage is `!member <uni_id>`.'.format(
                ctx.message.author.mention))
    elif isinstance(error, commands.errors.BadArgument):
        return await ctx.message.channel.send('{0} - Your university id should be a 7 digit integer.'.format(
            ctx.message.author.mention))
    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.message.delete()
        return await ctx.message.channel.send('{0} - This command is now run in DMs with the Bot.'.format(
            ctx.message.author.mention))


# Create_website_user command.
#
# Run the command to create users on the website.
#
# This command uses the subprocesses module to run the command which creates users on the website and sends out the
# welcome emails.
#
# Only the webmaster can use this command and it must be in the web-development channel.
#
# For this command to work the bot must be running on the same machine as the website.
@bot.command(pass_context=True)
@commands.has_role(bot_data.ROLE_IDS['webmaster'])
@commands.check(web_development_channel_check)
async def website_create_users(ctx):
    process = subprocess.Popen(config.website_create_users_command.split(), stdout=subprocess.PIPE)
    # The command will either print the number of new members or the error that occurred when trying to make the
    # accounts.
    output, _ = process.communicate()
    return await ctx.message.channel.send('{0} - Command output: `{1}`.'.format(
        ctx.message.author.mention, output.decode('utf-8').strip('\n')))


# Create_website_user command error handler.
@website_create_users.error
async def on_website_create_users_error(ctx, error):
    if isinstance(error, commands.errors.MissingRole):
        return await ctx.message.channel.send(
            '{0} - Only the webmaster can use this command.'.format(
                ctx.message.author.mention))
    elif isinstance(error, commands.errors.CheckFailure):
        return await ctx.message.channel.send('{0} - You must use this command in the web-development channel.'.format(
            ctx.message.author.mention))


# Prune command.
#
# Prunes up to 100 messages.
#
# Only exec can use this command.
@bot.command(pass_context=True)
@commands.has_role(bot_data.ROLE_IDS['exec'])
async def prune(ctx, prune_amount: int):
    if prune_amount > 100:
        return await ctx.message.channel.send(
            '{0} - You can only prune up to 100 messages at once.'.format(
                ctx.message.author.mention))
    elif prune_amount < 0:
        return await ctx.message.channel.send(
            '{0} - The amount of messages to prune must be a postive integer.'.format(
                ctx.message.author.mention))

    deleted = await ctx.message.channel.purge(limit=prune_amount)
    return await ctx.message.channel.send('{0} - Pruned {1} messages.'.format(
        ctx.message.author.mention, len(deleted)), delete_after=5)


# Prune command error handler.
@prune.error
async def on_prune_error(ctx, error):
    if isinstance(error, commands.errors.MissingRole):
        return await ctx.message.channel.send(
            '{0} - Only the exec can use this command.'.format(
                ctx.message.author.mention))
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        return await ctx.message.channel.send(
            '{0} - You are using this command incorrectly. The correct usage is `!prune <amount>`.'.format(
                ctx.message.author.mention))
    elif isinstance(error, commands.errors.BadArgument):
        return await ctx.message.channel.send(
            '{0} - The amount of messages to prune must be a postive integer.'.format(
                ctx.message.author.mention))


# Submit_karaoke_history command.
#
# Takes a karaoke history file (produced by vocaluxe-history https://github.com/Danalite/vocaluxe-history) and stores
# a record of the songs that were sung at the event. It does not
#
# Only the av can use this command.
@bot.command(pass_context=True, aliases=['skh'])
@commands.has_role(bot_data.ROLE_IDS['av'])
async def submit_karaoke_history(ctx, date: str, *, event: str):
    if len(ctx.message.attachments) == 0:
        return await ctx.message.channel.send(
            '{0} - You must attach the karaoke history file.'.format(ctx.message.author.mention))

    attachment_url = ctx.message.attachments[0].url
    file_request = requests.get(attachment_url)
    history_entries = file_request.text.split('\n')[:-1]
    for entry in history_entries:
        try:
            _, title, artist = entry.strip().split('\t')
        except (ValueError):
            continue

        conn = sqlite3.connect(bot_data.DATABASE_PATH)
        try:
            conn.execute(
                ('INSERT INTO KARAOKE_HISTORY VALUES (:title, :artist, :date, :event)'),
                {'title': title, 'artist': artist, 'date': date, 'event': event}
            )
        except (sqlite3.IntegrityError):
            pass
        conn.commit()
        conn.close()

    return await ctx.message.channel.send('{0} - History file processed.'.format(ctx.message.author.mention))


# Submit_karaoke_history command error handler.
@submit_karaoke_history.error
async def on_submit_karaoke_history_error(ctx, error):
    if isinstance(error, commands.errors.MissingRole):
        return await ctx.message.channel.send(
            '{0} - Only the AV can use this command.'.format(
                ctx.message.author.mention))
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        return await ctx.message.channel.send(
            ('{0} - You are using this command incorrectly. The correct usage is'
             ' `!submit_karaoke_history <eventDate> <eventName>`. <eventDate> must be "YYMMDD".'
             ' You must also attach the history file.').format(
                ctx.message.author.mention))
    else:
        await ctx.message.channel.send(
            '{0} - There was an error processing this command.'.format(ctx.message.author.mention))
        webmaster = ctx.message.guild.get_role(bot_data.ROLE_IDS['webmaster'])
        web_development_channel = bot.get_guild(bot_data.GUILD_ID).get_channel(bot_data.CHANNEL_IDS['web-development'])
        return await web_development_channel.send(
            ('{0} - There was an error with the karaoke history command.\n'
             '```{1}```').format(webmaster.mention, error))


# Lastsang command.
#
# Returns the last time a given song was sung at Karaoke.
@bot.command(pass_context=True)
@commands.check(bot_commands_channel_check)
async def lastsang(ctx, *, title: str):
    conn = sqlite3.connect(bot_data.DATABASE_PATH)
    cur = conn.execute(
        ('SELECT title, artist, eventName, MAX(eventDate) FROM KARAOKE_HISTORY WHERE title LIKE ?'
         ' GROUP BY title, artist LIMIT 5;'),
        (title + '%',)
    )
    rows = cur.fetchall()
    if not rows:
        return await ctx.message.channel.send(
            '{0} - No record for that song was found'.format(ctx.message.author.mention))

    songs = []
    for row in rows:
        song_title, artist, event_name, event_date = row
        event_datetime = datetime.strptime(event_date, '%y%m%d')
        song_data = (song_title, artist, event_name, datetime.strftime(event_datetime, '%d/%m/%y'))
        songs.append(song_data)

    response = '{0} - ' if len(songs) == 1 else '{0}:\n'
    response = response.format(ctx.message.author.mention)

    for song in songs:
        response += '*{0}* by *{1}* was last sung at **{2}** ({3})\n'.format(*song)

    return await ctx.message.channel.send(response)


# lastsang command error handler.
@lastsang.error
async def on_lastsang_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        pass
    else:
        await ctx.message.channel.send(
            '{0} - There was an error processing this command.'.format(ctx.message.author.mention))
        webmaster = ctx.message.guild.get_role(bot_data.ROLE_IDS['webmaster'])
        web_development_channel = bot.get_guild(bot_data.GUILD_ID).get_channel(bot_data.CHANNEL_IDS['web-development'])
        return await web_development_channel.send(
            ('{0} - There was an error with the lastsang command.\n'
             '```{1}```').format(webmaster.mention, error))


# sang command.
#
# Returns all the times a given song was sung at Karaoke.
@bot.command(pass_context=True)
@commands.check(bot_commands_channel_check)
async def sang(ctx, *, title: str):
    conn = sqlite3.connect(bot_data.DATABASE_PATH)
    cur = conn.execute(('SELECT * FROM KARAOKE_HISTORY WHERE title LIKE ?'
                        ' ORDER BY title, artist, eventDate DESC LIMIT 15;'), (title + '%',))
    rows = cur.fetchall()
    
    if not rows:
        return await ctx.message.channel.send(
            '{0} - No record for that song was found'.format(ctx.message.author.mention))

    songs = []
    for row in rows:
        song_title, artist, event_date, event_name = row
        event_datetime = datetime.strptime(event_date, '%y%m%d')
        song_data = (song_title, artist, event_name, datetime.strftime(event_datetime, '%d/%m/%y'))
        songs.append(song_data)

    response = '{0} - ' if len(songs) == 1 else '{0}:\n'
    response = response.format(ctx.message.author.mention)

    for song in songs:
        response += '*{0}* by *{1}* was sung at **{2}** ({3})\n'.format(*song)

    return await ctx.message.channel.send(response)


# sang command error handler.
@sang.error
async def on_sang_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        pass
    else:
        await ctx.message.channel.send(
            '{0} - There was an error processing this command.'.format(ctx.message.author.mention))
        webmaster = ctx.message.guild.get_role(bot_data.ROLE_IDS['webmaster'])
        web_development_channel = bot.get_guild(bot_data.GUILD_ID).get_channel(bot_data.CHANNEL_IDS['web-development'])
        return await web_development_channel.send(
            ('{0} - There was an error with the sang command.\n'
             '```{1}```').format(webmaster.mention, error))


# topartists command.
#
# Returns the top artists from karaoke.
@bot.command(pass_context=True)
@commands.check(bot_commands_channel_check)
@commands.check(web_development_channel_check)
async def topartists(ctx):
    conn = sqlite3.connect(bot_data.DATABASE_PATH)
    cur = conn.execute(('SELECT artist, COUNT(*) FROM KARAOKE_HISTORY GROUP BY artist'
                        ' ORDER BY COUNT(*) DESC LIMIT 10;'))
    rows = cur.fetchall()

    response = '{0}:\n'
    response = response.format(ctx.message.author.mention)

    for row in rows:
        response += 'Songs by *{0}* have been sung **{1}** times.\n'.format(*row)

    return await ctx.message.channel.send(response)


# topsongs command.
#
# Returns the top songs from karaoke.
@bot.command(pass_context=True)
@commands.check(bot_commands_channel_check)
async def topsongs(ctx):
    conn = sqlite3.connect(bot_data.DATABASE_PATH)
    cur = conn.execute(('SELECT title, artist, COUNT(*) FROM KARAOKE_HISTORY GROUP BY title, artist'
                        ' ORDER BY COUNT(*) DESC LIMIT 10;'))
    rows = cur.fetchall()

    response = '{0}:\n'
    response = response.format(ctx.message.author.mention)

    for row in rows:
        response += '*{0}* by *{1}* has been sung **{2}** times.\n'.format(*row)

    return await ctx.message.channel.send(response)


# topby command.
#
# Returns the most sung songs by a given artist at Karaoke.
@bot.command(pass_context=True)
@commands.check(bot_commands_channel_check)
async def topby(ctx, *, artist: str):
    conn = sqlite3.connect(bot_data.DATABASE_PATH)
    cur = conn.execute(('SELECT title, artist, COUNT(*) AS song_count FROM KARAOKE_HISTORY WHERE artist LIKE ?'
                        ' GROUP BY title HAVING song_count > 0 ORDER BY song_count DESC LIMIT 15;'), (artist + '%',))
    rows = cur.fetchall()
    if not rows:
        return await ctx.message.channel.send(
            '{0} - No songs from this artist have been played/No records for this artist was found'.format(ctx.message.author.mention))

    totalTimes = 0
    songs = []
    for row in rows:
        song_title, artist_name, count = row
        song_data = (song_title, artist_name, count)
        songs.append(song_data)
        totalTimes += count

    response = '{0}:\n' 
    response = response.format(ctx.message.author.mention)
    response += f'In total, songs by **{rows[0][1]}** have been sung **{totalTimes}** times.\n'
    for song in songs:
        response += '*{0}* has been sung **{2}** time(s)\n'.format(*song)

    return await ctx.message.channel.send(response)

# topby command error handler.
@topby.error
async def on_topby_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        pass
    else:
        await ctx.message.channel.send(
            '{0} - There was an error processing this command.'.format(ctx.message.author.mention))
        webmaster = ctx.message.guild.get_role(bot_data.ROLE_IDS['webmaster'])
        web_development_channel = bot.get_guild(bot_data.GUILD_ID).get_channel(bot_data.CHANNEL_IDS['web-development'])
        return await web_development_channel.send(
            ('{0} - There was an error with the topby command.\n'
             '```{1}```').format(webmaster.mention, error))

# Events command.
#
# Returns a formatted list of upcoming events.
#
# This command was implemented in the old Animadeus bot, however no one ever really used it so this is a very low
# priority feature.
@bot.command(pass_context=True)
@commands.check(bot_commands_channel_check)
async def events(ctx):
    message_string = ('{0} - This command is not currently implemented'
                      ' ~~and probably wont be for a very long time~~.')
    return await ctx.message.channel.send(message_string.format(
        ctx.message.author.mention))


# Library command.
#
# Returns a formatted list of library titles that match a search string.
#
# This command was implemented in the old Animadeus bot, however no one ever really used it so this is a very low
# priority feature.
@bot.command(pass_context=True)
@commands.check(bot_commands_channel_check)
async def library(ctx):
    message_string = ('{0} - This command is not currently implemented'
                      ' ~~and probably wont be for a very long time~~.')
    return await ctx.message.channel.send(message_string.format(
        ctx.message.author.mention))


# Coin Flip command.
#
# Returns either heads or tails.
@bot.command(pass_context=True)
async def coinflip(ctx):
    outcome = random.choice(['Heads', 'Tails'])
    return await ctx.message.channel.send('{0} - {1}'.format(
        ctx.message.author.mention, outcome))


if __name__ == '__main__':
    bot.add_cog(OffTopicCog(bot))
    bot.run(config.bot_token)
