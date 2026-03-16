import aiosqlite
import nextcord
from nextcord.ext.commands import Cog

import config
from utils import checks


class ViewDatabaseCommand(Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="starboard_view", description="(DEV) View starboard database"
    )
    async def starboard_view(self, interaction: nextcord.Interaction):
        if not await checks.require_dev(interaction):
            return

        try:
            async with aiosqlite.connect("bot_data.db") as db:
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
