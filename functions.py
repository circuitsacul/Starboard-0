import db_handler as dbh
from discord import utils
import discord
import asyncio
from asyncio import Lock, sleep
from copy import deepcopy


async def is_starboard_emoji(guild_id, emoji_str):
    for starboard in dbh.database.db['guilds'][guild_id]['channels']:
        if emoji_str in dbh.database.db['guilds'][guild_id]['channels'][starboard]['emojis']:
            return True
    return False


async def get_emoji(guild, emoji):
    try:
        if type(emoji) is str:
            split_emoji = emoji.split(':')
            if len(split_emoji) > 2:
                emoji_id = int(split_emoji[2].replace('>', ''))
            else:
                emoji_id = int(split_emoji[0])
        else:
            emoji_id = emoji
        emoji_obj = utils.get(guild.emojis, id=emoji_id)
        if emoji_obj is not None:
            return emoji_obj
    except:
        pass
    return emoji


async def get_emoji_str(guild, emojis):
    emoji_string = ''
    for emoji in emojis:
        obj = await get_emoji(guild, emoji)
        emoji_string += f"{obj} "
    return emoji_string


async def get_prefix(bot, message):
    if message.guild is None:
        return discord.ext.commands.when_mentioned_or('sb ')(bot, message)
    prefix = dbh.database.db['guilds'][message.guild.id]['prefix'].lower()
    return discord.ext.commands.when_mentioned_or(prefix)(bot, message)


async def parse_user(guild_id, user_id, bot):
    if guild_id not in dbh.database.db['guilds']:
        return False
    parse = False
    if user_id not in dbh.database.db['profiles']:
        parse = True
    elif 'bot' not in dbh.database.db['profiles'][user_id]:
        parse = True
    if parse:
        guild = bot.get_guild(guild_id)
        user = utils.get(guild.members, id=user_id)
        if user is None:
            user = utils.get(bot.get_all_members(), id=user_id)
        dbh.database.db['profiles'][user_id] = {
            'guild_stats': {}
            }
        if user is not None:
            dbh.database.db['profiles'][user_id]['bot'] = user.bot
        else:
            dbh.database.db['profiles'][user_id]['bot'] = False
    if guild_id not in dbh.database.db['profiles'][user_id]['guild_stats']:
        dbh.database.db['profiles'][user_id]['guild_stats'][guild_id] = {
            'on_starboard': 0,
            'given_stars': 0,
            'received_stars': 0
        }
    return True


async def parse_leaderboard(guild_id, user_id):
    recv_dict = {'user': user_id, 'points': dbh.database.db['profiles'][user_id]['guild_stats'][guild_id]['received_stars']}
    give_dict = {'user': user_id, 'points': dbh.database.db['profiles'][user_id]['guild_stats'][guild_id]['given_stars']}
    on_sb_dict = {'user': user_id, 'points': dbh.database.db['profiles'][user_id]['guild_stats'][guild_id]['on_starboard']}

    new_lb = deepcopy(dbh.database.db['guilds'][guild_id]['leaderboard']['top_recv'])
    for x, d in enumerate(new_lb):
        if d['user'] == user_id or d['points'] <= 0:
            del new_lb[x]
    if recv_dict['points'] > 0:
        new_lb.append(recv_dict)
    new_lb = sorted(new_lb, key=lambda d: d['points'], reverse=True)
    if len(new_lb) > 10:
        new_lb.pop(0)
    dbh.database.db['guilds'][guild_id]['leaderboard']['top_recv'] = new_lb

    new_lb = deepcopy(dbh.database.db['guilds'][guild_id]['leaderboard']['top_givers'])
    for x, d in enumerate(new_lb):
        if d['user'] == user_id or d['points'] <= 0:
            del new_lb[x]
    if give_dict['points'] > 0:
        new_lb.append(give_dict)
    new_lb = sorted(new_lb, key=lambda d: d['points'], reverse=True)
    if len(new_lb) > 10:
        new_lb.pop(0)
    dbh.database.db['guilds'][guild_id]['leaderboard']['top_givers'] = new_lb

    new_lb = deepcopy(dbh.database.db['guilds'][guild_id]['leaderboard']['top_on_sb'])
    for x, d in enumerate(new_lb):
        if d['user'] == user_id or d['points'] <= 0:
            del new_lb[x]
    if on_sb_dict['points'] > 0:
        new_lb.append(on_sb_dict)
    new_lb = sorted(new_lb, key=lambda d: d['points'], reverse=True)
    if len(new_lb) > 10:
        new_lb.pop(0)
    dbh.database.db['guilds'][guild_id]['leaderboard']['top_on_sb'] = new_lb


async def award_give_star(guild_id, user_id, points, bot):
    done = await parse_user(guild_id, user_id, bot)
    if not done:
        return
    if dbh.database.db['profiles'][user_id]['bot']:
        return
    dbh.database.db['profiles'][user_id]['guild_stats'][guild_id]['given_stars'] += points
    dbh.database.db['guilds'][guild_id]['leaderboard']['total_given'] += points
    await parse_leaderboard(guild_id, user_id)


async def award_receive_star(guild_id, user_id, points, bot):
    done = await parse_user(guild_id, user_id, bot)
    if not done:
        return
    if dbh.database.db['profiles'][user_id]['bot']:
        return
    dbh.database.db['profiles'][user_id]['guild_stats'][guild_id]['received_stars'] += points
    dbh.database.db['guilds'][guild_id]['leaderboard']['total_recv'] += points
    await parse_leaderboard(guild_id, user_id)


async def award_on_starboard(guild_id, user_id, points, bot):
    done = await parse_user(guild_id, user_id, bot)
    if not done:
        return
    if dbh.database.db['profiles'][user_id]['bot']:
        return
    dbh.database.db['profiles'][user_id]['guild_stats'][guild_id]['on_starboard'] += points
    await parse_leaderboard(guild_id, user_id)


async def recount_stars(guild, channel, message_id, bot):
    if (channel.id, message_id) not in dbh.database.db['guilds'][guild.id]['messages']:
        dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)] = {'emojis': {}, 'links': {}}
    try:
        message = await channel.fetch_message(message_id)
    except Exception as e:
        return True
    if message is not None:
        for emoji in message.reactions:
            if emoji.emoji not in dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)]['emojis']:
                dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)]['emojis'][emoji.emoji] = {}
            async for user in emoji.users():
                dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)]['emojis'][emoji.emoji][user.id] = True

    for starboard_id, link_message_id in dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)]['links'].items():
        starboard = utils.get(guild.channels, id=starboard_id)
        if starboard is None:
            continue
        try:
            link_message = await starboard.fetch_message(link_message_id)
        except Exception as e:
            continue
        for emoji in link_message.reactions:
            if emoji.emoji not in dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)]['emojis']:
                dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)]['emojis'][emoji.emoji] = {}
            async for user in emoji.users():
                dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)]['emojis'][emoji.emoji][user.id] = True
    await update_message(guild.id, channel.id, message_id, bot)

    return False


async def get_embed_from_message(message):
    nsfw = message.channel.is_nsfw()
    embed = discord.Embed(colour=0xFCFF00)
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    embed_text = ''
    msg_attachments = message.attachments
    urls = []

    for attachment in msg_attachments:
        urls.append((attachment.filename, attachment.url))

    for msg_embed in message.embeds:
        if msg_embed.type == 'rich':
            fields = [(f"\n**{x.name}**\n", f"{x.value}\n") for x in msg_embed.fields]
            embed_text += f"__**{msg_embed.title}**__\n"
            embed_text += f"{msg_embed.description}\n"
            for name, value in fields:
                embed_text += name + value
        elif msg_embed.type == 'image':
            if msg_embed.url != discord.Embed.Empty:
                urls.append(("Embeded Image", msg_embed.url))
        elif msg_embed.type == 'gifv':
            if msg_embed.url != discord.Embed.Empty:
                urls.append(("Embeded GIF", msg_embed.url))
        elif msg_embed.type == 'video':
            if msg_embed.url != discord.Embed.Empty:
                urls.append(("Embeded Video", msg_embed.url))

    value_string = f"{message.content}\n{embed_text}"
    context_string = f"\n[**Jump to Message**]({message.jump_url})"
    if len(value_string + context_string) >= 1000:
        full_string = value_string[0:800] + "... *message clipped*\n" + context_string
    else:
        full_string = value_string + context_string
    embed.add_field(name=f'Message{" (NSFW)" if nsfw else ""}', value=full_string)

    if len(urls) > 0:
        url_string = ''
        current = 0
        for item in urls:
            url_string += f"[**{item[0]}**]({item[1]})\n"
            if item[1].endswith('png') or item[1].endswith('jpg') or item[1].endswith('jpeg'):
                if current == 0:
                    embed.set_image(url=item[1])
                    current += 1
                elif current == 1:
                    embed.set_thumbnail(url=item[1])
                    current += 1
        embed.add_field(name='Attachments', value=url_string, inline=False)

    embed.set_footer(text=f"{message.id} • {str(message.created_at).split(' ', 1)[0].replace('-', '/')}")

    return embed


async def new_link_message(original_message, starboard_channel, points, emojis):
    if original_message is None:
        return
    original_channel = original_message.channel
    guild = original_message.guild
    embed = await get_embed_from_message(original_message)
    sent = await starboard_channel.send(f"**{points} points | {original_channel.mention}**", embed=embed)
    dbh.database.db['guilds'][guild.id]['messages'][(original_channel.id, original_message.id)]['links'][starboard_channel.id] = sent.id
    dbh.database.db['guilds'][guild.id]['channels'][starboard_channel.id]['messages'][sent.id] = (original_channel.id, original_message.id)
    for emoji_str in emojis:
        emoji = await get_emoji(guild, emoji_str)
        try:
            await sent.add_reaction(emoji)
        except Exception as e:
            pass


async def update_link_message(guild, original_message, link_message, points, emojis, link_edits, original_channel_id):
    if original_message is not None and link_edits:
        original_channel = original_message.channel
        embed = await get_embed_from_message(original_message)
        await link_message.edit(content=f"**{points} points | {original_channel.mention}**", embed=embed)
    elif original_message is None:
        await link_message.edit(content=f"**{points} points | <#{original_channel_id}>**")
    else:
        original_channel = original_message.channel
        await link_message.edit(content=f"**{points} points | {original_channel.mention}**")
    for emoji_str in emojis:
        emoji = await get_emoji(guild, emoji_str)
        try:
            await link_message.add_reaction(emoji)
        except Exception as e:
            pass


async def handle_starboard(guild, channel_id, starboard_id, deleted, message_id, message, bot):
    starboard = utils.get(guild.channels, id=starboard_id)
    if starboard is None:
        return

    starboard_settings = dbh.database.db['guilds'][guild.id]['channels'][starboard_id]
    if message is not None:
        if not starboard.is_nsfw() and message.channel.is_nsfw():
            return

    if starboard_id in dbh.database.db['guilds'][guild.id]['messages'][(channel_id, message_id)]['links']:
        link_message_id = dbh.database.db['guilds'][guild.id]['messages'][(channel_id, message_id)]['links'][starboard_id]
        try:
            link_message = await starboard.fetch_message(link_message_id)
        except Exception as e:
            link_message = None
        if deleted and dbh.database.db['guilds'][guild.id]['channels'][starboard_id]['link_deletes']:
            await link_message.delete()
    else:
        link_message = None

    user_dict = {}
    if guild.id not in dbh.database.locks:
        dbh.database.locks[guild.id] = Lock()
    async with dbh.database.locks[guild.id]:
        for emoji_name, user_ids in dbh.database.db['guilds'][guild.id]['messages'][(channel_id, message_id)]['emojis'].items():
            if emoji_name in starboard_settings['emojis']:
                for user_id in user_ids:
                    await parse_user(guild.id, user_id, bot)
                    if user_id in dbh.database.db['profiles']:
                        if dbh.database.db['profiles'][user_id]['bot']:
                            continue
                    else:
                        user_object = utils.get(guild.members, id=user_id)
                        if user_object is None:
                            continue
                        if user_object.bot:
                            dbh.database.db['profiles'][user_id]['bot'] = True
                            continue
                        else:
                            dbh.database.db['profiles'][user_id]['bot'] = False
                    if not starboard_settings['self_star'] and user_id == dbh.database.db['guilds'][guild.id]['messages'][(channel_id, message_id)]['author']:
                        continue
                    user_dict[user_id] = True

    points = len(user_dict)

    remove = False
    add = False
    if points >= starboard_settings['required_stars']:
        add = True
    elif points <= starboard_settings['required_to_lose']:
        remove = True

    if link_message is not None:
        if remove:
            await link_message.delete()
            if message is not None:
                await award_on_starboard(guild.id, message.author.id, -1, bot)
        else:
            link_edits = starboard_settings['link_edits']
            try:
                await update_link_message(guild, message, link_message, points, starboard_settings['emojis'], link_edits, channel_id)
            except discord.errors.NotFound:
                pass
    elif add:
        if message is not None:
            await award_on_starboard(guild.id, message.author.id, 1, bot)
        await new_link_message(message, starboard, points, starboard_settings['emojis'])


async def handle_media_channel(guild, channel_id, message):
    settings = dbh.database.db['guilds'][guild.id]['media_channels'][channel_id]

    is_valid = True

    if settings['media_only']:
        if len(message.attachments) == 0:
            is_valid = False

        if not is_valid:
            string = f"{message.author.mention}, that channel is a media-only channel. Only messages with attachments are allowed."
            try:
                await message.delete()
            except Exception as e:
                pass
            await message.author.send(string)
            return

    for emoji_str in settings['emojis']:
        emoji = await get_emoji(guild, emoji_str)
        try:
            await message.add_reaction(emoji)
        except Exception as e:
            pass

    return is_valid


async def update_message(guild_id, channel_id, message_id, bot):
    # check if everything exists
    guild = bot.get_guild(guild_id)
    channel = utils.get(guild.channels, id=channel_id)

    deleted = False
    if channel is not None:
        try:
            message = await channel.fetch_message(message_id)
            dbh.database.db['guilds'][guild_id]['messages'][(channel_id, message_id)]['author'] = message.author.id
        except Exception as e:
            deleted = True
            message = None
    else:
        deleted = True
        message = None

    # handle other message logic
    for starboard_id in dbh.database.db['guilds'][guild_id]['channels']:
        asyncio.create_task(handle_starboard(guild, channel_id, starboard_id, deleted, message_id, message, bot))
