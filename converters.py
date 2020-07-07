from discord.ext.commands import Converter
from discord import utils
from discord import TextChannel


class ChannelElseInt(Converter):
    async def convert(self, ctx, argument):
        stripped = argument.replace('>', '').replace('<', '').replace('#', '')
        try:
            channel_id = int(stripped)
        except ValueError:
            return None
        channel = utils.get(ctx.guild.channels, id=channel_id)
        if channel is not None:
            return channel
        return channel_id