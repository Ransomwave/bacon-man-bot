import nextcord
from nextcord.ext import commands

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
        await starboard.create_starboard_table()


def setup(bot):
    bot.add_cog(OnReady(bot))
