import nextcord
from nextcord.ext.commands import Cog


class PingCommand(Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: nextcord.Interaction):
        latency = round(self.bot.latency * 1000)  # Convert to milliseconds
        await interaction.response.send_message(f"Pong! Latency: {latency}ms")


def setup(bot):
    bot.add_cog(PingCommand(bot))
