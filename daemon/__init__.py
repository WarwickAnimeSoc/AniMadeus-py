from datetime import datetime

import discord
from discord.ext import commands

import bot_data
import config

async def setup_daemon(bot: commands.Bot):

    # Startup event.
    #
    # Currently only sets the status.
    @bot.event
    async def on_ready():
        await bot.change_presence(activity=config.status_activity)


    # Event listener for member joins.
    #
    # Used to welcome new users.
    @bot.listen()
    async def on_member_join(member):
        guild = bot.get_guild(bot_data.GUILD_ID)
        assert guild is not None, "server must exist"

        newcomers_channel = guild.get_channel(bot_data.CHANNEL_IDS['newcomers'])
        welcome_channel = guild.get_channel(bot_data.CHANNEL_IDS['welcome-and-links'])
        rules_channel = guild.get_channel(bot_data.CHANNEL_IDS['rules'])
        role_channel = guild.get_channel(bot_data.CHANNEL_IDS['role-assign'])
        welcome_string = ('Welcome to the Warwick Anime and Manga Society Discord server, {0}!'
                          ' Please see {1} and {2} for information about the society and this server.'
                          ' To gain access to the rest of the server please react to the message in {3}!')

        assert isinstance(newcomers_channel, discord.TextChannel)
        assert isinstance(welcome_channel, discord.TextChannel)
        assert isinstance(rules_channel, discord.TextChannel)
        assert isinstance(role_channel, discord.TextChannel)
        
        await newcomers_channel.send(
            welcome_string.format(member.mention, welcome_channel.mention, rules_channel.mention, role_channel.mention))


    # Event listener for reaction adds.
    #
    # Used for the role assign system.
    @bot.listen()
    async def on_raw_reaction_add(payload):
        if payload.message_id == bot_data.MESSAGE_IDS['role_assign_message']:
            await on_general_role_assignment_add(payload)    


    # Event listener for reaction adds.
    #
    # Used for the role assign system.
    @bot.listen()
    async def on_raw_reaction_remove(payload):    
        if payload.message_id == bot_data.MESSAGE_IDS['role_assign_message']:
            await on_general_role_assignment_remove(payload)


    # Event listener for reaction adds.
    #
    # Used for the role assign system in #role-assign.
    async def on_general_role_assignment_add(payload):
        try:
            # If we start using custom emoji this will need editing
            role_id = bot_data.EMOJI_TO_ROLE_MAPPINGS[str(payload.emoji)]
        except KeyError:
            return

        guild = bot.get_guild(bot_data.GUILD_ID)
        assert guild is not None

        role = guild.get_role(role_id)
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

        guild = bot.get_guild(bot_data.GUILD_ID)
        assert guild is not None

        role = guild.get_role(role_id)
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        try:
            await member.remove_roles(role)
        except discord.HTTPException:
            pass


