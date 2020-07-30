import discord, db_handler as dbh, asyncio, sys
from discord.ext.commands import Bot
from discord.ext import commands
from discord import utils
from asyncio import sleep, Lock
from cs_cog import Settings
from owner_cog import Owner
from util_cog import Utility
from lb_cog import Leaderboard
from pretty_help import PrettyHelp
import functions
import converters
from secrets import TOKEN, BETA_TOKEN, OWNER_ID, INVITE, SUPPORT_SERVER, SUPPORT_ID, SUGGESTION_CHANNEL

PREFIXES = functions.get_prefix
BETA_PREFIXES = functions.get_prefix

DOWNVOTE = '⬇️'
UPVOTE = '⬆️'

if len(sys.argv) > 1:
    if sys.argv[1].lower() == 'beta':
        bot = Bot(command_prefix=BETA_PREFIXES, help_command=PrettyHelp(color=0xFCFF00))
else:
    bot = Bot(command_prefix=PREFIXES, help_command=PrettyHelp(color=0xFCFF00))

running = True
database = None


async def loop_save():
    while dbh.database.db is None:
        await sleep(5)
    while running:
        await sleep(60)
        dbh.database.save_database()


@bot.command(
    name='about', brief='About Starboards',
    description='Give quick description of what a starboard is and what it is for'
)
async def about_starbot(ctx):
    msg = """
    StarBot is a Discord starboard bot.\
    Starboards are kind of like democratic pins.\
    A user can "vote" to have a message displayed on a channel by reacting with an emoji, usually a star.\
    A Starboard is a great way to archive funny messages.\
    """
    embed=discord.Embed(
        title='About StarBot and Starboards',
        description=msg, color=0xFCFF00
    )
    await ctx.send(embed=embed)


@commands.cooldown(2, 120, commands.BucketType.user)
@bot.command(
    name='suggest', aliases=['suggestion'],
    description='Send a suggestion to the bot creator to report a bug or suggest a change/feature',
    brief='Send suggestion to bot creator'
    )
async def suggest(ctx, *, suggestion):
    if ctx.message.author.bot:
        return
    support_guild = bot.get_guild(SUPPORT_ID)
    suggestion_channel = utils.get(support_guild.channels, id=SUGGESTION_CHANNEL)

    embed = discord.Embed(title='Suggestion', description=suggestion)
    embed.set_author(name=ctx.message.author, icon_url=ctx.message.author.avatar_url)
    sent = await suggestion_channel.send(embed=embed)
    await sent.add_reaction(emoji=UPVOTE)
    await sent.add_reaction(emoji=DOWNVOTE)
    await ctx.send(f"{ctx.author.mention}, your suggestion has been sent!")


@bot.command(
    name='ping', aliases=['latency'], description='Get bot latency',
    brief='Get bot latency'
    )
async def ping(ctx):
    await ctx.send('Pong! {0} ms'.format(round(bot.latency*1000, 3)))

@bot.command(
    name='links', aliases=['support', 'server', 'invite'], description='Get helpful links',
    brief='Get helpful links'
    )
async def links(ctx):
    embed = discord.Embed(title='Helpful Links', colour=0xFCFF00)
    embed.description = f"[**Add me to your server**]({INVITE})\
        \n[**Join the support server**]({SUPPORT_SERVER})\
        \n[**View documentation**](https://circuitsacul.github.io/StarBot/)\
        \n[**View source code**](https://github.com/CircuitSacul/StarBot)"
    await ctx.send(ctx.message.author.mention, embed=embed)

@bot.command(name='info', aliases=['botstats'], description='Bot stats', brief='Bot stats')
async def stats_for_bot(ctx):
    owner = bot.get_user(OWNER_ID)
    if ctx.author.id == OWNER_ID:
        owner_string = "You!"
    else:
        owner_string = owner
    embed = discord.Embed(
        title='Bot Stats', colour=0xFCFF00,
        description = f"""
        **Owner:** {owner_string}
        **Guilds:** {len(bot.guilds)}
        **Users:** {len(bot.users)}
        **Ping:** {round(bot.latency*1000, 3)} ms
        """
        )
    await ctx.send(ctx.message.author.mention, embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if ctx.author.bot:
        return
    elif type(error) is discord.ext.commands.errors.CommandNotFound:
        return
    elif type(error) is discord.ext.commands.errors.BadArgument:
        pass
    elif type(error) is discord.ext.commands.errors.MissingRequiredArgument:
        pass
    elif type(error) is discord.ext.commands.errors.NoPrivateMessage:
        pass
    elif type(error) is discord.ext.commands.errors.MissingPermissions:
        pass
    elif str(error).startswith('Command raised an exception: Forbidden'):
        error = "I don't have the necessary permissions to do that :("
    else:
        embed = discord.Embed(title='Error!', description='An unexpected error ocurred. Please report this to the dev.', color=discord.Color.red())
        embed.add_field(name='Error Message:', value=f"```{type(error)}:\n{error}```")
        print(f"Error: {error}")
        await ctx.send(embed=embed)
        return
    embed = discord.Embed(title='Oops!', description=f"```{error}```", color=discord.Color.orange())
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    global database
    dbh.set_database(bot)
    bot.loop.create_task(loop_save())
    print(f"Logged in as {bot.user.name} in {len(bot.guilds)} guilds!")
    await bot.change_presence(
        status=discord.Status.online
        #activity=discord.Game('Mention me for help')
        )


@bot.event
async def on_guild_join(guild):
    dbh.database.add_guild(guild.id)


@bot.event
async def on_guild_remove(guild):
    pass


@bot.event
async def on_raw_reaction_add(payload):
    guild_id = payload.guild_id
    channel_id = payload.channel_id
    message_id = payload.message_id
    user_id = payload.user_id
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    user = utils.get(guild.members, id=user_id)
    channel = utils.get(guild.channels, id=channel_id)
    message = await channel.fetch_message(message_id)
    if user.bot:
        return

    if payload.emoji.id is not None:
        emoji_str = payload.emoji.id
    else:
        emoji_str = payload.emoji.name

    if await functions.is_starboard_emoji(guild_id, emoji_str):
        await functions.award_give_star(guild_id, user_id, 1, bot)
        await functions.award_receive_star(guild_id, message.author.id, 1, bot)

    if guild_id not in dbh.database.locks:
        dbh.database.locks[guild_id] = Lock()
    async with dbh.database.locks[guild_id]:
        if channel_id not in dbh.database.db['guilds'][guild_id]['channels']:
            if (channel_id, message_id) not in dbh.database.db['guilds'][guild_id]['messages']:
                dbh.database.db['guilds'][guild_id]['messages'][(channel_id, message_id)] = {'emojis': {}, 'links': {}}
            if emoji_str not in dbh.database.db['guilds'][guild_id]['messages'][(channel_id, message_id)]['emojis']:
                dbh.database.db['guilds'][guild_id]['messages'][(channel_id, message_id)]['emojis'][emoji_str] = {}
            dbh.database.db['guilds'][guild_id]['messages'][(channel_id, message_id)]['emojis'][emoji_str][user_id] = True

            await functions.update_message(guild_id, channel_id, message_id, bot)
        else:
            if message_id in dbh.database.db['guilds'][guild_id]['channels'][channel_id]['messages']:
                original_channel_id, original_message_id = dbh.database.db['guilds'][guild_id]['channels'][channel_id]['messages'][message_id]
                if (original_channel_id, original_message_id) not in dbh.database.db['guilds'][guild_id]['messages']:
                    dbh.database.db['guilds'][guild_id]['messages'][(original_channel_id, original_message_id)] = {'emojis': {}, 'links': {}}
                if emoji_str not in dbh.database.db['guilds'][guild_id]['messages'][(original_channel_id, original_message_id)]['emojis']:
                    dbh.database.db['guilds'][guild_id]['messages'][(original_channel_id, original_message_id)]['emojis'][emoji_str] = {}
                dbh.database.db['guilds'][guild_id]['messages'][(original_channel_id, original_message_id)]['emojis'][emoji_str][user_id] = True

                await functions.update_message(guild_id, original_channel_id, original_message_id, bot)


@bot.event
async def on_raw_reaction_remove(payload):
    guild_id = payload.guild_id
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel_id = payload.channel_id
    message_id = payload.message_id
    user_id = payload.user_id
    user = utils.get(guild.members, id=user_id)
    channel = utils.get(guild.channels, id=channel_id)
    message = await channel.fetch_message(message_id)
    if user.bot:
        return

    if payload.emoji.id is not None:
        emoji_str = payload.emoji.id
    else:
        emoji_str = payload.emoji.name

    if await functions.is_starboard_emoji(guild_id, emoji_str):
        await functions.award_give_star(guild_id, user_id, -1, bot)
        await functions.award_receive_star(guild_id, message.author.id, -1, bot)

    if guild_id not in dbh.database.locks:
        dbh.database.locks[guild_id] = Lock()
    async with dbh.database.locks[guild_id]:
        if channel_id not in dbh.database.db['guilds'][guild_id]['channels']:
            if (channel_id, message_id) not in dbh.database.db['guilds'][guild_id]['messages']:
                dbh.database.db['guilds'][guild_id]['messages'][(channel_id, message_id)] = {'emojis': {}, 'links': {}}
            if emoji_str not in dbh.database.db['guilds'][guild_id]['messages'][(channel_id, message_id)]['emojis']:
                dbh.database.db['guilds'][guild_id]['messages'][(channel_id, message_id)]['emojis'][emoji_str] = {}
            if user_id in dbh.database.db['guilds'][guild_id]['messages'][(channel_id, message_id)]['emojis'][emoji_str]:
                del dbh.database.db['guilds'][guild_id]['messages'][(channel_id, message_id)]['emojis'][emoji_str][user_id]

            await functions.update_message(guild_id, channel_id, message_id, bot)

        else:
            if message_id in dbh.database.db['guilds'][guild_id]['channels'][channel_id]['messages']:
                original_channel_id, original_message_id = dbh.database.db['guilds'][guild_id]['channels'][channel_id]['messages'][message_id]
                if emoji_str not in dbh.database.db['guilds'][guild_id]['messages'][(original_channel_id, original_message_id)]['emojis']:
                    dbh.database.db['guilds'][guild_id]['messages'][(original_channel_id, original_message_id)]['emojis'][emoji_str] = {}
                if user_id in dbh.database.db['guilds'][guild_id]['messages'][(original_channel_id, original_message_id)]['emojis'][emoji_str]:
                    del dbh.database.db['guilds'][guild_id]['messages'][(original_channel_id, original_message_id)]['emojis'][emoji_str][user_id]

                await functions.update_message(guild_id, original_channel_id, original_message_id, bot)


@bot.event
async def on_raw_message_delete(payload):
    guild_id = payload.guild_id
    channel_id = payload.channel_id
    message_id = payload.message_id

    if guild_id not in dbh.database.locks:
        guild = bot.get_guild(guild_id)
        if guild is None:
            return
        dbh.database.locks[guild_id] = Lock()
    async with dbh.database.locks[guild_id]:
        if channel_id not in dbh.database.db['guilds'][guild_id]['channels']:
            if (channel_id, message_id) in dbh.database.db['guilds'][guild_id]['messages']:
                await functions.update_message(guild_id, channel_id, message_id, bot)


@bot.event
async def on_message_edit(ctx, message):
    if ctx.guild is None:
        return
    guild_id = ctx.guild.id
    channel_id = ctx.channel.id
    message_id = message.id

    if guild_id not in dbh.database.locks:
        dbh.database.locks[guild_id] = Lock()
    async with dbh.database.locks[guild_id]:
        if channel_id not in dbh.database.db['guilds'][guild_id]['channels']:
            if (channel_id, message_id) in dbh.database.db['guilds'][guild_id]['messages']:
                await functions.update_message(guild_id, channel_id, message_id, bot)


@bot.event
async def on_message(message):
    is_valid = True

    if message.guild is not None:
        prefix = dbh.database.db['guilds'][message.guild.id]['prefix']
        if message.channel.id in dbh.database.db['guilds'][message.guild.id]['media_channels']:
            is_valid = await functions.handle_media_channel(message.guild, message.channel.id, message)
    else:
        prefix = 'sb '

    if message.author.bot:
        return

    if message.content != '' and is_valid:
        if bot.user.mention == message.content.split()[0].replace('!', '') and len(message.content.split()) == 1:
            await message.channel.send(f"The prefix here is `{prefix}`\nCall `{prefix}help` for help with commands or `{prefix}links` for helpful links.")
        else:
            await bot.process_commands(message)



try:
    bot.add_cog(Settings(bot))
    bot.add_cog(Owner(bot))
    bot.add_cog(Utility(bot))
    bot.add_cog(Leaderboard(bot))
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'beta':
            bot.run(BETA_TOKEN)
    else:
        bot.run(TOKEN)
finally:
    running = False
    dbh.database.save_database()
    print("logging out")
