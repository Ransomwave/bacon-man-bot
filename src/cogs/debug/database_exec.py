import nextcord
from nextcord.ext.commands import Cog

import config
from utils import checks
from utils.truncate_str import truncate_to_discord_max_length


async def run_sql_command(command: str):
    import aiosqlite

    async with aiosqlite.connect("bot_data.db") as db:
        cursor = await db.execute(command)
        result = await cursor.fetchall()
        await db.commit()
        print(f"Executed SQL command: {command} with result: {result}")
    return result


class DatabaseExecCommand(Cog):
    def __init__(self, bot: nextcord.Client):
        self.bot = bot

    @nextcord.slash_command(name="database_exec", description="(DEV) Executes any SQL")
    async def database_exec(
        self,
        interaction: nextcord.Interaction,
        command: str = nextcord.SlashOption(
            name="command", description="The SQL command to execute", required=True
        ),
    ):
        if not await checks.require_dev(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        result = await run_sql_command(command)
        result_text = str(result)
        await interaction.edit_original_message(
            content=f"Result:\n```sql\n{truncate_to_discord_max_length(result_text)}\n```"
        )


def setup(bot: nextcord.Client):
    bot.add_cog(DatabaseExecCommand(bot))
