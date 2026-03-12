import nextcord
from nextcord.ext.commands import Cog

import config


class OnMemberJoinEvent(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id not in config.AVAILABLE_IN_GUILDS:
            return

        general_channel = self.bot.get_channel(995400838849769508)

        await general_channel.send(
            f"{member.mention} just joined. Say hi to them!", delete_after=600
        )


def setup(bot):
    bot.add_cog(OnMemberJoinEvent(bot))
