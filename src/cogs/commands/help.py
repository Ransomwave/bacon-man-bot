import nextcord
from nextcord.ext import commands
from nextcord.ext.commands import Cog


class HelpCommand(Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="help", description="View all commands")
    async def help(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Help - List of Commands",
            description="Here are all the available commands:",
            color=nextcord.Color.blue(),
        )

        # Pull registered application (slash) commands from the bot instance.
        command: commands.Command
        for command in self.bot.get_all_application_commands():

            if "(DEV)" in command.description:
                continue  # Skip commands marked as DEV-only

            description = command.description or "No description provided."
            embed.add_field(
                name=f"/{command.name}",
                value=description,
                inline=False,
            )

        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(HelpCommand(bot))
