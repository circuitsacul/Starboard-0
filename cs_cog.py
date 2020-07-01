import discord, db_handler as dbh, copy
from asyncio import Lock
from discord.ext import commands
from typing import Union


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.group(
        name='defaults', aliases=['d'], description='Set the default settings when starboards are added',
        brief='Manage default starboard settings'
        )
    @commands.guild_only()
    async def defaults(self, ctx):
        if ctx.author.bot:
            return
        if ctx.invoked_subcommand == None:
            settings = dbh.database.db['guilds'][ctx.guild.id]['default_settings']
            msg = ''
            msg += f"requiredStars: {settings['required_stars']}\n"
            msg += f"requiredToLose: {settings['required_to_lose']}\n"
            msg += f"selfStar: {settings['self_star']}\n"
            msg += f"linkEdits: {settings['link_edits']}\n"
            msg += f"linkDeletes: {settings['link_deletes']}\n"
            await ctx.send(msg)


    @defaults.command(
        name='selfstar', aliases=['ss'], description='Set the default for allowing self-stars',
        brief='Set default for self-star'
        )
    @commands.has_permissions(manage_channels=True)
    async def toggle_self_star(self, ctx, self_star: bool):
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            dbh.database.db['guilds'][ctx.guild.id]['default_settings']['self_star'] = self_star
        await ctx.send(f"Set selfStar to {self_star}.")


    @defaults.command(
        name='requiredstars', aliases=['rs'], description='Set the default for minimum stars for message',
        brief='Set default for required-stars'
        )
    @commands.has_permissions(manage_channels=True)
    async def required_stars(self, ctx, count: int):
        if count <= dbh.database.db['guilds'][ctx.message.guild.id]['default_settings']['required_to_lose']:
            await ctx.send("requiredStars cannot be less than or equal to requiredToLose")
            return
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            dbh.database.db['guilds'][ctx.guild.id]['default_settings']['required_stars'] = count
        await ctx.send(f"The default for requiredStars has been set to {count}")


    @defaults.command(
        name='requiredtolose', aliases=['rtl'], defaults='Set the default for maximum stars before message is removed',
        brief='Set default for required-to-lose'
        )
    @commands.has_permissions(manage_channels=True)
    async def required_to_lose(self, ctx, count: int):
        if count >= dbh.database.db['guilds'][ctx.message.guild.id]['default_settings']['required_stars']:
            await ctx.send("requiredToLose cannot be greater than or equal to requiredStars.")
            return
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            dbh.database.db['guilds'][ctx.message.guild.id]['default_settings']['required_to_lose'] = count
        await ctx.send(f"The default for requiredToLose has been set to {count}.")

    @defaults.command(
        name='linkedits', aliases=['le'], description='Set the default for linking message edits',
        brief='Set default for link-deletes'
        )
    @commands.has_permissions(manage_channels=True)
    async def toggle_link_edits(self, ctx, link_edits: bool):
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            dbh.database.db['guilds'][ctx.message.guild.id]['default_settings']['link_edits'] = link_edits
        await ctx.send(f"The default for linkEdits has been set to {link_edits}")

    @defaults.command(
        name='linkdeletes', aliases=['ld'], description='Set the default for linking message deletes',
        brief='Set default for link-edits'
        )
    @commands.has_permissions(manage_channels=True)
    async def toggle_link_deletes(self, ctx, link_deletes: bool):
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            dbh.database.db['guilds'][ctx.message.guild.id]['default_settings']['link_deletes'] = link_deletes
        await ctx.send(f"The default for linkDeletes has been set to {link_deletes}")


    @commands.group(
        name='starboard', aliases=['s'], invoke_without_command=True, description='Managed starboards',
        brief='Manage starboards'
        )
    @commands.guild_only()
    async def channel(self, ctx, channel:discord.TextChannel=None):
        if ctx.author.bot:
            return
        if ctx.invoked_subcommand == None:
            msg = ''
            if channel is None:
                settings = dbh.database.db['guilds'][ctx.guild.id]['channels']
                if ctx.guild.id not in dbh.database.locks:
                    dbh.database.locks[ctx.guild.id] = Lock()
                async with dbh.database.locks[ctx.guild.id]:
                    for channel_id in dbh.database.db['guilds'][ctx.guild.id]['channels']:
                        channel_object = discord.utils.get(ctx.guild.channels, id=channel_id)
                        if channel_object is None:
                            msg += f"Deleted Channel; ChannelID: {channel_id}\n"
                            continue
                        msg += f"{channel_object.mention}: {settings[channel_id]['emojis']}\n"
            else:
                settings = dbh.database.db['guilds'][ctx.guild.id]['channels']
                channel_object = discord.utils.get(ctx.guild.channels, id=channel.id)
                msg += f"{channel_object.mention}: {settings[channel.id]['emojis']}\n"
                msg += f"----requiredStars: {settings[channel.id]['required_stars']}\n"
                msg += f"----requiredToLose: {settings[channel.id]['required_to_lose']}\n"
                msg += f"----selfStar: {settings[channel.id]['self_star']}\n"
                msg += f"----linkEdits: {settings[channel.id]['link_edits']}\n"
                msg += f"----linkDeletes: {settings[channel.id]['link_deletes']}\n"
            if msg == '':
                msg = 'No starboards have been set. Use `sb.channel add #channel_name` to add one.'
            await ctx.send(msg)


    @channel.command(
        name='selfstar', aliases=['ss'], description='Set self-star for specific starboard',
        brief='Set self-star for starboard'
        )
    @commands.has_permissions(manage_channels=True)
    async def channel_self_star(self, ctx, channel: discord.TextChannel, allow: bool):
        if channel == None:
            await ctx.send("I could not find any channel with that name or id")
            return
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]['self_star'] = allow
        await ctx.send(f"Set selfStar to {allow} for {channel.mention}")


    @channel.command(
        name='linkedits', aliases=['le'], description='Set link-edits for specific starboard',
        brief='Set link-edits for starboard'
        )
    @commands.has_permissions(manage_channels=True)
    async def channel_link_edits(self, ctx, channel: discord.TextChannel, link_edits: bool):
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]['link_edits'] = link_edits
        await ctx.send(f"Set linkEdits to {link_edits} for {channel.mention}")


    @channel.command(
        name='linkdeletes', aliases=['ld'], description='Set link-deletes for specific starboard',
        brief='Set link-deletes for starboard'
        )
    @commands.has_permissions(manage_channels=True)
    async def channel_link_deletes(self, ctx, channel: discord.TextChannel, link_deletes: bool):
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]['link_deletes'] = link_deletes
        await ctx.send(f"Set linkDeletes to {link_deletes} for {channel.mention}")


    @channel.command(
        name='add', aliases=['+', 'a'], description='Add a new starboard',
        brief='Add starboard'
        )
    @commands.has_permissions(manage_channels=True)
    async def add_channel(self, ctx, channel: discord.TextChannel):
        if channel == None:
            await ctx.send("I could not find any channel with that name or id")
            return

        try:
            dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]
        except KeyError:
            if ctx.guild.id not in dbh.database.locks:
                dbh.database.locks[ctx.guild.id] = Lock()
            async with dbh.database.locks[ctx.guild.id]:
                dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id] = copy.deepcopy(dbh.database.db['guilds'][ctx.guild.id]['default_settings'])
                dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]['emojis'] = []
                dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]['messages'] = {}
            await ctx.send(f"Added starboard {channel.mention}")
            return
        await ctx.send(f"{channel.mention} is already a starboard")


    @channel.command(
        name='remove', aliases=['-', 'delete', 'd', 'r'], description='Remove a starboard',
        brief='Remove starboard'
        )
    @commands.has_permissions(manage_channels=True)
    async def remove_channel(self, ctx, channel: discord.TextChannel):
        if channel == None:
            await ctx.send("I could not find any channel with that name or id")
            return

        try:
            if ctx.guild.id not in dbh.database.locks:
                dbh.database.locks[ctx.guild.id] = Lock()
            async with dbh.database.locks[ctx.guild.id]:
                del dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]
            await ctx.send(f"{channel.mention} is no longer a starboard")
        except KeyError:
            await ctx.send("That channel is not a starboard")


    @channel.group(
        name='emoji', aliases=['e'], description='Manage emojis for specific starboard',
        brief='Manage emojis'
        )
    @commands.has_permissions(manage_channels=True)
    async def emoji(self, ctx):
        if ctx.author.bot:
            return


    @emoji.command(
        name='add', aliases=['+', 'a'], description='Add emoji for specific starboard',
        brief='Add emoji'
        )
    async def add_emoji(self, ctx, channel: discord.TextChannel, emoji):
        try:
            if ctx.guild.id not in dbh.database.locks:
                dbh.database.locks[ctx.guild.id] = Lock()
            async with dbh.database.locks[ctx.guild.id]:
                dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]['emojis'].append(emoji)
            await ctx.send(f"Added {emoji} to {channel.mention}")
        except KeyError:
            await ctx.send(f"{channel.mention} is not a starboard.")


    @emoji.command(
        name='remove', aliases=['-', 'r'], description='Removed emoji for specific starboard',
        brief='Remove emoji'
        )
    async def remove_emoji(self, ctx, channel: discord.TextChannel, emoji):
        try:
            if ctx.guild.id not in dbh.database.locks:
                dbh.database.locks[ctx.guild.id] = Lock()
            async with dbh.database.locks[ctx.guild.id]:
                if emoji in dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]['emojis']:
                    for x, i in enumerate(dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]['emojis']):
                        if i == emoji:
                            dbh.database.db['guilds'][ctx.guild.id]['channels'][channel.id]['emojis'].pop(x)
            await ctx.send(f"Removed {emoji} from {channel.mention}")
        except KeyError:
            await ctx.send(f"Either {emoji} is not linked to {channel.mention} or {channel.mention} is not a starboard.")


    @channel.command(
        name='requiredstars', aliases=['rs'], description='Set minimum stars for message to appear on starboard for specific starboard',
        brief='Set required-stars for starboard'
        )
    @commands.has_permissions(manage_channels=True)
    async def channel_required_stars(self, ctx, channel: discord.TextChannel, count: int):
        if channel == None:
            await ctx.send("I could not find any channel with that name or id")
            return
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            if count <= dbh.database.db['guilds'][ctx.message.guild.id]['channels'][channel.id]['required_to_lose']:
                await ctx.send("requiredStars cannot be less than or equal to requiredToLose")
                return
            dbh.database.db['guilds'][ctx.message.guild.id]['channels'][channel.id]['required_stars'] = count
        await ctx.send(f"Set requiredStars to {count}")


    @channel.command(
        name='requiredtolose', aliases=['rtl'], description='Set minimum stars before message is removed for specific starboard',
        brief='Set required-to-lose for starboard'
        )
    @commands.has_permissions(manage_channels=True)
    async def channel_required_to_lose(self, ctx, channel: discord.TextChannel, count: int):
        if channel == None:
            await ctx.send("I could not find any channel with that name or id")
            return
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            if count >= dbh.database.db['guilds'][ctx.message.guild.id]['channels'][channel.id]['required_stars']:
                await ctx.send("requiredToLose cannot be greater than or equal to requiredStars")
                return
            dbh.database.db['guilds'][ctx.message.guild.id]['channels'][channel.id]['required_to_lose'] = count
        await ctx.send(f"requiredToLose has been set to {count}")

    @commands.group(
        name='mediachannel', aliases=['mc'], description='Manage media channels, where the bot automatically reacts to messages with an emoji.',
        brief='Manage media channels', invoke_without_command=True
        )
    @commands.guild_only()
    async def media_channels(self, ctx, channel: discord.TextChannel=None):
        string = ''
        if channel is None:
            if ctx.guild.id not in dbh.database.locks:
                dbh.database.locks[ctx.guild.id] = Lock()
            async with dbh.database.locks[ctx.guild.id]:
                for media_channel_id in dbh.database.db['guilds'][ctx.guild.id]['media_channels']:
                    media_channel = discord.utils.get(ctx.guild.channels, id=media_channel_id)
                    if media_channel is None:
                        del dbh.database.db['guilds'][ctx.guild.id]['media_channels'][media_channel_id]
                        continue
                    emojis = dbh.database.db['guilds'][ctx.guild.id]['media_channels'][media_channel_id]['emojis']
                    string += f"{media_channel.mention}: {emojis}\n"
                if string == '':
                    string = "You have no media channels set. Use `sb mediachannel add <channel>` to add one."
        else:
            settings = dbh.database.db['guilds'][ctx.guild.id]['media_channels'][channel.id]
            emojis = settings['emojis']
            string = f"{channel.mention}: {emojis}\n----mediaOnly: {settings['media_only']}"
        await ctx.send(string)

    @media_channels.command(
        name='add', aliases=['a', '+'], brief='Add a media channel', description='Add a media channel'
    )
    @commands.has_permissions(manage_channels=True)
    async def add_media_channel(self, ctx, channel: discord.TextChannel):
        if channel is None:
            await ctx.send("I could not find a channel with that name or id")
            return
        if channel.id in dbh.database.db['guilds'][ctx.guild.id]['media_channels']:
            await ctx.send("That is already a media channel")
            return
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            dbh.database.db['guilds'][ctx.guild.id]['media_channels'][channel.id] = {
                'emojis': [],
                'media_only': False
            }
            await ctx.send("Added media channel")

    @media_channels.command(
        name='remove', aliases=['r', '-'], brief='Remove media channel', description='Remove media channel'
    )
    @commands.has_permissions(manage_channels=True)
    async def remove_media_channel(self, ctx, channel: discord.TextChannel):
        if channel is None:
            await ctx.send("I could not find a channel with that name or id")
            return
        #if isinstance(channel, int):
        #    channel = discord.utils.get(ctx.guild.channels, id=channel)
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            if channel.id not in dbh.database.db['guilds'][ctx.guild.id]['media_channels']:
                await ctx.send("That does not appear to be a media channel")
                return
            del dbh.database.db['guilds'][ctx.guild.id]['media_channels'][channel.id]
            await ctx.send(f"{channel.mention} is no longer a media channel")

    @media_channels.command(
        name='addemoji', aliases=['ae'], brief='Add an emoji to media channel',
        description='Adds an emoji for the bot to automatically react to all messages sent in the media channel'
    )
    @commands.has_permissions(manage_channels=True)
    async def media_channel_add_emoji(self, ctx, channel: discord.TextChannel, emoji):
        if channel is None:
            await ctx.send("I could not find a channel with that name or id")
            return
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            if channel.id not in dbh.database.db['guilds'][ctx.guild.id]['media_channels']:
                await ctx.send("That is not a media channel")
                return
            dbh.database.db['guilds'][ctx.guild.id]['media_channels'][channel.id]['emojis'].append(emoji)
            await ctx.send(f"Added {emoji} to {channel.mention}")

    @media_channels.command(
        name='removeemoji', aliases=['re'], brief='Remove an emoji from media channel',
        description='Remove an emoji from media channel'
    )
    @commands.has_permissions(manage_channels=True)
    async def media_channel_remove_emoji(self, ctx, channel: discord.TextChannel, emoji):
        if channel is None:
            await ctx.send("I could not find a channel with that name or id")
            return
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            if channel.id not in dbh.database.db['guilds'][ctx.guild.id]['media_channels']:
                await ctx.send("That is not a media channel")
                return
            if emoji not in dbh.database.db['guilds'][ctx.guild.id]['media_channels'][channel.id]['emojis']:
                await ctx.send("That emoji does not appear to be in the media channel")
                return
            dbh.database.db['guilds'][ctx.guild.id]['media_channels'][channel.id]['emojis'].remove(emoji)
            await ctx.send(f"Removed {emoji} from {channel.mention}")

    @media_channels.command(
        name='mediaonly', aliases=['mo', 'imagesonly'], brief='Set mediaOnly for media channel',
        description='Set wether or not a media channel allows messages without images'
    )
    @commands.has_permissions(manage_channels=True, manage_messages=True)
    async def media_channel_media_only(self, ctx, channel: discord.TextChannel, allow: bool):
        if channel is None:
            await ctx.send("I could not find a channel with that name or id")
            return
        if ctx.guild.id not in dbh.database.locks:
            dbh.database.locks[ctx.guild.id] = Lock()
        async with dbh.database.locks[ctx.guild.id]:
            if channel.id not in dbh.database.db['guilds'][ctx.guild.id]['media_channels']:
                await ctx.send("That is not a media channel")
                return
            dbh.database.db['guilds'][ctx.guild.id]['media_channels'][channel.id]['media_only'] = allow
            await ctx.send(f"Set mediaOnly to {allow} for {channel.mention}")