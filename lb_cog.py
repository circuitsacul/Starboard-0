import db_handler as dbh, discord
from discord.ext import commands
from discord import utils
import functions
import asyncio
from asyncio import Lock


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def user_ids_to_mentions(self, user_ids):
        string = ''
        for uid in user_ids:
            string += f"**<@{uid['user']}>: {uid['points']}**"
            if uid is not user_ids[-1]: string += '\n'
        return string if string != '' else 'No one...'

    @commands.command(
        name='user', aliases=['u'], brief='View stats for a user',
        description="View the total number of given and receive stars, as well as the number of times they've been on the starboard."
    )
    @commands.guild_only()
    async def user_leaderboard(self, ctx, user:discord.Member=None):
        if user is None:
            user = ctx.message.author
        await functions.parse_user(ctx.guild.id, user.id, self.bot)
        profile = dbh.database.db['profiles'][user.id]['guild_stats'][ctx.guild.id]
        embed = discord.Embed(
            color=0xFCFF00,
            title=f"Stats for {str(user)}"
        )
        embed.add_field(name="Total Stars Given:", value=f"{profile['given_stars']}", inline=False)
        embed.add_field(name="Total Stars Received:", value=f"{profile['received_stars']}", inline=False)
        embed.add_field(name="Total Times on Starboard:", value=f"{profile['on_starboard']}", inline=False)
        await ctx.send(embed=embed)

    @commands.group(
        name='leaderboard', aliases=['lb', 'top'], brief='View leaderboard',
        description='Viw top users and total stars received and given in a server',
        invoke_without_command=True
    )
    @commands.guild_only()
    async def guild_leaderboard(self, ctx):
        lb = dbh.database.db['guilds'][ctx.guild.id]['leaderboard']
        embed = discord.Embed(title='Leaderboard', color=0xFCFF00)
        embed.add_field(name='Top Star Receivers', value=await self.user_ids_to_mentions(lb['top_recv']), inline=False)
        embed.add_field(name='Top Star Givers', value=await self.user_ids_to_mentions(lb['top_givers']), inline=False)
        embed.add_field(name='Top on Starboard', value=await self.user_ids_to_mentions(lb['top_on_sb']), inline=False)
        embed.add_field(name='Other Stats', value=f"**Total Stars Given: {lb['total_given']}**", inline=False)
        await ctx.send(embed=embed)

    @guild_leaderboard.command(
        name='reset', brief='Reset Leaderboard', description='Reset Leaderboard'
    )
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def reset_leaderboard(self, ctx):
        def check(message):
            print("Check Called")
            if message.author.id != ctx.message.author.id:
                return False
            if message.content == ctx.message.content:
                return False
            return True

        await ctx.send("Type \"confirm\" to cofirm resetting the database.")
        
        try:
            message = await self.bot.wait_for('message', check=check)
        except asyncio.TimeoutError:
            await ctx.send("Timed Out!")
        else:
            if message.content.lower() == 'confirm':
                if ctx.guild.id not in dbh.database.locks:
                    dbh.database.locks[ctx.guild.id] = Lock()
                async with dbh.database.locks[ctx.guild.id]:
                    dbh.database.db['guilds'][ctx.guild.id]['leaderboard'] = {
                        'top_givers': [],
                        'top_recv': [],
                        'top_on_sb': [],
                        'total_given': 0,
                        'total_recv': 0
                    }
                    for user in ctx.guild.members:
                        if user.id not in dbh.database.db['profiles']:
                            continue
                        dbh.database.db['profiles'][user.id]['guild_stats'][ctx.guild.id] = {
                            'on_starboard': 0,
                            'given_stars': 0,
                            'received_stars': 0
                        }
                await functions.parse_leaderboard(ctx.guild.id, ctx.message.author.id)
                await ctx.send("Done!")
            else:
                await ctx.send("Cancelling.")