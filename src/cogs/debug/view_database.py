import aiosqlite
import nextcord
from nextcord.ext.commands import Cog

import config


class ViewDatabaseCommand(Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="view_database", description="(DEV) View starboard database"
    )
    async def view_database(self, interaction: nextcord.Interaction):
        if interaction.user.id != config.DEV_ID:  # Replace with your Discord user ID
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        try:
            async with aiosqlite.connect("starboard.db") as db:
                cursor = await db.execute("SELECT * FROM starboard")
                rows = await cursor.fetchall()
                await cursor.close()
        except Exception as e:
            await interaction.response.send_message(
                f"Failed to query database: {e}", ephemeral=True
            )
            return

        if not rows:
            await interaction.response.send_message(
                "The starboard database is empty.", ephemeral=True
            )
            return

        message = "Starboard rows:\n"
        for amount, (message_id, starboard_message_id) in enumerate(rows):
            if amount >= 10:
                message += "_And more..._\n"
                break
            message += f"Message ID: {message_id}, Starboard Message ID: {starboard_message_id}\n"

        await interaction.response.send_message(message, ephemeral=True)


def setup(bot):
    bot.add_cog(ViewDatabaseCommand(bot))
