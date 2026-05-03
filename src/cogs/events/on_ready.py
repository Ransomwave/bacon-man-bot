import nextcord
from nextcord.ext import commands

from cogs.commands import autoreact, mediachannel, reaction_roles
from . import starboard


class OnReady(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("=============== RUNNING ===============")
        print(f"Logged in as {self.client.user} (ID: {self.client.user.id})")
        print("=======================================")

        activity = nextcord.Activity(
            type=nextcord.ActivityType.watching, name="Ransomwave's Games"
        )

        await self.client.change_presence(
            status=nextcord.Status.online, activity=activity
        )
        await starboard.setup_db_table()
        await reaction_roles.setup_db_table()
        await autoreact.setup_db_table()
        await mediachannel.setup_db_table()


def setup(bot):
    bot.add_cog(OnReady(bot))
