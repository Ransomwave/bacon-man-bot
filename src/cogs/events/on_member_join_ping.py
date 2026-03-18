import nextcord
from nextcord.ext.commands import Cog

import config


class OnMemberJoinPing(Cog):

    ID_GENERAL = 995400838849769508
    ID_ROLES = 1481865040901443717

    def __init__(self, bot: nextcord.Client):
        self.bot = bot

    async def get_text_channel(self, channel_id: int):
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.get_channel(channel_id)
            except (nextcord.NotFound, nextcord.Forbidden, nextcord.HTTPException):
                self.bot.logger.exception(
                    f"Failed to fetch channel with ID {channel_id}"
                )
                return None

        if isinstance(channel, nextcord.TextChannel):
            return channel

        self.bot.logger.error(f"Channel with ID {channel_id} is not a text channel")
        return None

    @Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        if member.guild.id not in config.AVAILABLE_IN_GUILDS:
            return

        channel_general = await self.get_text_channel(self.ID_GENERAL)
        channel_roles = await self.get_text_channel(self.ID_ROLES)

        if channel_general is None or channel_roles is None:
            self.bot.logger.error(
                "One or more channels could not be found. Skipping on member join ping."
            )
            return

        await channel_general.send(
            f"{member.mention} just joined. Say hello!", delete_after=600
        )

        await channel_roles.send(f"{member.mention}", delete_after=2)


def setup(bot: nextcord.Client):
    bot.add_cog(OnMemberJoinPing(bot))
