import nextcord
from nextcord.ext.commands import Cog

import config
from utils import thread_utils


class CloseBugThreadCommand(Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="close",
        description="Close the current Bug Report thread. Additionally, you can also lock the channel.",
    )
    async def close(
        self,
        interaction: nextcord.Interaction,
        reason: str = nextcord.SlashOption(
            name="reason",
            description="Reason for closing the thread",
            choices=["Fixed", "AlreadyFixed", "NotBug", "Closed", "Duplicate"],
        ),
        lockedBool: bool = nextcord.SlashOption(
            name="locked",
            description="Whether to lock the thread after closing it",
            default=False,
            required=False,
        ),
    ):
        # Check if the command is being used in a thread
        if not isinstance(interaction.channel, nextcord.Thread):
            await interaction.response.send_message(
                f"This command can only be used in a thread.",
                ephemeral=True,
            )
            return

        thread = interaction.channel

        # Check if the thread is in the bug report forum
        if thread.parent_id != config.BUG_REPORT_CHANNEL:
            await interaction.response.send_message(
                f"This command can only be used in <#{config.BUG_REPORT_CHANNEL}> threads.",
                ephemeral=True,
            )
            return

        # Check if the user has permission to close threads
        if interaction.user.id != config.DEV_ID and not any(
            role.permissions.manage_threads for role in interaction.user.roles
        ):
            await interaction.response.send_message(
                "You don't have permission to close this thread.", ephemeral=True
            )
            return

        try:
            # Remove the "Open" tag if it exists
            await thread_utils.remove_tag(thread, config.BUG_REPORT_TAGS["Open"])

            # Apply the closure reason tag
            await thread_utils.apply_tag(thread, config.BUG_REPORT_TAGS[reason])

            # Send confirmation message
            embed = nextcord.Embed(
                title="Thread Closed",
                description=f"This thread has been closed with reason: **{reason}**",
                color=0xFF4747,
            )
            embed.set_footer(
                text=f"Closed by {interaction.user.display_name}",
                icon_url=interaction.user.avatar.url,
            )

            await interaction.response.send_message(embed=embed)

            # Close the thread
            await thread.edit(archived=True, locked=lockedBool)

            print(
                f"Thread '{thread.name}' closed by {interaction.user.name} with reason: {reason}"
            )

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while closing the thread: {str(e)}", ephemeral=True
            )
            print(f"Error closing thread '{thread.name}': {e}")


def setup(bot):
    bot.add_cog(CloseBugThreadCommand(bot))
