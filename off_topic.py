# Extra commands for #off-topic.
import bot_data

import discord
from discord.ext import commands
import re
import random

FFXIV_SHILL = ('Have you heard of the critically acclaimed MMORPG Final Fantasy XIV with an expanded free'
               ' trial which you can play through the entirety of A Realm Reborn and the award winning Heavensward expansion'
               ' and also award winning Stormblood expansion up to level 70 for free with no restrictions on playtime.')

FFXIV_STRINGS = [
    'ff14',
    'ffxiv',
    'thancred',
    'eorzea',
    'elidibus',
    'emet',
    'fantasy',
    'noscea'
]

FFXIV_EXPR = re.compile(r'\b(?:{0})\b'.format('|'.join(FFXIV_STRINGS)), re.IGNORECASE)

DEROGATORY_WORD_STRINGS = [
    'bad',
    'cringe',
    'mid',
    'overrated',
    'shit',
    'awful',
    'crap',
    'boring',
    'terrible',
    'worst',
    'annoying'
]

DEROGATORY_EXPR = re.compile(r'\b(?:{0})\b'.format('|'.join(DEROGATORY_WORD_STRINGS)), re.IGNORECASE)

LIN_FILE = 'https://i.imgur.com/D217yoj.jpg'


# Cog containing specific commands/features for the #off-topic channel.
class OffTopicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.ffxiv_cooldown = 100  # Number of messages before a reply.
        self.ffxiv_counter = 0  # Current message count.

    # Event listener for off-topic messages.
    @commands.Cog.listener('on_message')
    async def check_message(self, message):
        if message.channel.id == bot_data.CHANNEL_IDS['off-topic'] and not message.author.bot:
            # Hamilton Meme reply
            #
            # Author: Maybe
            if (("hamilton" in message.content.lower() or "lin manuel miranda" in message.content.lower())
                  and re.search(DEROGATORY_EXPR, message.content)):
                ctx = await self.bot.get_context(message)
                await ctx.reply(LIN_FILE)

        elif not message.author.bot:
            # Akechi react
            #
            # Author: Mabey
            if 'akechi' in message.content.lower():
                await message.add_reaction('☝️')

            # FFXIV shill message.
            #
            # Author: Mabey
            if re.search(FFXIV_EXPR, message.content):
                if self.ffxiv_counter == 0:
                    ctx = await self.bot.get_context(message)
                    await ctx.reply(FFXIV_SHILL)

                self.ffxiv_counter = (self.ffxiv_counter + 1) % self.ffxiv_cooldown

    # Bravo Nolan command.
    #
    # Author: Danalite
    #
    # Quotes kino.
    @commands.command(pass_context=True)
    async def bravonolan(self, ctx):
        quote = ''
        while quote == '':
            quote = random.choice((open("./data/bravonolan.txt").readlines()))
        await ctx.reply(quote)
