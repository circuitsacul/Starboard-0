import db_handler as dbh, discord
from discord.ext import commands
from discord import utils
import functions


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
            title=f"Stats for {str(user)}",
            description=f"**Total Stars Given: {profile['given_stars']}\
                \nTotal Stars Received: {profile['received_stars']}\
                \nTotal Times on Starboard: {profile['on_starboard']}**"
        )
        await ctx.send(embed=embed)

    @commands.command(
        name='leaderboard', aliases=['lb', 'top'], brief='View leaderboard',
        description='Viw top users and total stars received and given in a server'
    )
    async def guild_leaderboard(self, ctx):
        lb = dbh.database.db['guilds'][ctx.guild.id]['leaderboard']
        embed = discord.Embed(title='Leaderboard', color=0xFCFF00)
        embed.add_field(name='Top Star Receivers', value=await self.user_ids_to_mentions(lb['top_givers']))
        embed.add_field(name='Top Star Givers', value=await self.user_ids_to_mentions(lb['top_recv']), inline=True)
        embed.add_field(name='Top on Starboard', value=await self.user_ids_to_mentions(lb['top_on_sb']), inline=True)
        embed.add_field(name='Other Stats', value=f"**Total Stars Given: {lb['total_given']}**")
        await ctx.send(embed=embed)