import discord, db_handler as dbh
from asyncio import Lock
from discord.ext import commands
from discord import utils
from typing import Union
import functions


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command(
        name='recount', aliases=['count', 'update', 'rc', 'r'],
        description='Recount the emojis on a message as well as the linked messages on starboards',
        brief='Recount points on message'
        )
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def force_recount(self, ctx, channel: discord.TextChannel, message_id: int):
        if ctx.author.bot:
            return
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        if channel is not None:
            channel = channel.id
        else:
            await ctx.send("I could not find a channel with that name or id")
            return
        failed = False
        async with dbh.database.locks[ctx.guild.id]:
            if channel in dbh.database.db['guilds'][ctx.guild.id]['channels']:
                if message_id in dbh.database.db['guilds'][ctx.guild.id]['channels'][channel]['messages']:
                    original_channel_id, original_message_id = dbh.database.db['guilds'][ctx.guild.id]['channels'][channel]['messages'][message_id]
                    original_channel = utils.get(ctx.guild.channels, id=original_channel_id)
                    failed = await functions.recount_stars(ctx.guild, original_channel, original_message_id, self.bot)
                else:
                    failed = True
            else:
                channel_object = utils.get(ctx.guild.channels, id=channel)
                failed = await functions.recount_stars(ctx.guild, channel_object, message_id, self.bot)
        if failed:
            await ctx.send("Unable to recount stars on that message")
        else:
            await ctx.send("Done!")
