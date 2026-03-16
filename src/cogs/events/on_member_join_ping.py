import nextcord
from nextcord.ext.commands import Cog

import config


class OnMemberJoinPing(Cog):

    ID_GENERAL = 995400838849769508
    ID_ROLES = 1481865040901443717

    def __init__(self, bot: nextcord.Client):
        self.bot = bot
        self.channel_general = self.bot.get_channel(self.ID_GENERAL)
        self.channel_roles = self.bot.get_channel(self.ID_ROLES)

    @Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        if member.guild.id not in config.AVAILABLE_IN_GUILDS:
            return

        await self.channel_general.send(
            f"{member.mention} just joined. Say hello!", delete_after=600
        )

        await self.channel_roles.send(f"{member.mention}", delete_after=2)


def setup(bot: nextcord.Client):
    bot.add_cog(OnMemberJoinPing(bot))
