import db_handler as dbh
from discord import utils
import discord
import asyncio
from asyncio import Lock


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


async def award_give_star(guild_id, user_id, points, bot):
    done = await parse_user(guild_id, user_id, bot)
    if not done:
        return
    if dbh.database.db['profiles'][user_id]['bot']:
        return
    dbh.database.db['profiles'][user_id]['guild_stats'][guild_id]['given_stars'] += points


async def award_receive_star(guild_id, user_id, points, bot):
    done = await parse_user(guild_id, user_id, bot)
    if not done:
        return
    if dbh.database.db['profiles'][user_id]['bot']:
        return
    dbh.database.db['profiles'][user_id]['guild_stats'][guild_id]['received_stars'] += points


async def award_on_starboard(guild_id, user_id, points, bot):
    done = await parse_user(guild_id, user_id, bot)
    if not done:
        return
    if dbh.database.db['profiles'][user_id]['bot']:
        return
    dbh.database.db['profiles'][user_id]['guild_stats'][guild_id]['on_starboard'] += points


async def recount_stars(guild, channel, message_id, bot):
    if (channel.id, message_id) not in dbh.database.db['guilds'][guild.id]['messages']:
        dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)] = {'emojis': {}, 'links': {}}
    message = await channel.fetch_message(message_id)
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
            print(e)
            continue
        for emoji in link_message.reactions:
            if emoji.emoji not in dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)]['emojis']:
                dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)]['emojis'][emoji.emoji] = {}
            async for user in emoji.users():
                dbh.database.db['guilds'][guild.id]['messages'][(channel.id, message_id)]['emojis'][emoji.emoji][user.id] = True

    await update_message(guild.id, channel.id, message_id, bot)


async def get_embed_from_message(message):
    embed = discord.Embed(colour=0xFCFF00)
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    embed_text = ''
    msg_attachments = message.attachments
    urls = []

    for attachment in msg_attachments:
        urls.append((attachment.filename, attachment.url))

    for msg_embed in message.embeds:
        print(msg_embed.type)
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
        full_string = value_string[0:800] + "...\n*message clipped*\n" + context_string
    else:
        full_string = value_string + context_string
    embed.add_field(name='Message', value=full_string)

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
    for emoji in emojis:
        await sent.add_reaction(emoji)


async def update_link_message(original_message, link_message, points, emojis):
    if original_message is not None:
        original_channel = original_message.channel
        embed = await get_embed_from_message(original_message)
        await link_message.edit(content=f"**{points} points | {original_channel.mention}**", embed=embed)
    else:
        await link_message.edit(content=f"**{points} points | deleted**")
    for emoji in emojis:
        await link_message.add_reaction(emoji)


async def handle_starboard(guild, channel_id, starboard_id, deleted, message_id, message, bot):
    starboard = utils.get(guild.channels, id=starboard_id)
    if starboard is None:
        return

    nsfw = False
    starboard_settings = dbh.database.db['guilds'][guild.id]['channels'][starboard_id]
    if message is not None:
        if not starboard_settings['nsfw'] and message.channel.is_nsfw():
            nsfw = True
            return

    if starboard_id in dbh.database.db['guilds'][guild.id]['messages'][(channel_id, message_id)]['links']:
        link_message_id = dbh.database.db['guilds'][guild.id]['messages'][(channel_id, message_id)]['links'][starboard_id]
        try:
            link_message = await starboard.fetch_message(link_message_id)
        except Exception as e:
            print(e)
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
        else:
            await update_link_message(message, link_message, points, starboard_settings['emojis'])
    elif add:
        await new_link_message(message, starboard, points, starboard_settings['emojis'])


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
            print(e)
            deleted = True
            message = None
    else:
        deleted = True
        message = None

    # handle other message logic
    for starboard_id in dbh.database.db['guilds'][guild_id]['channels']:
        asyncio.create_task(handle_starboard(guild, channel_id, starboard_id, deleted, message_id, message, bot))
