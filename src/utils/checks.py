from typing import Literal

import nextcord

import config

type PermissionType = Literal["administrator", "manage_roles", "manage_guild"]


async def require_permission(
    interaction: nextcord.Interaction,
    permission: nextcord.Permissions,
) -> bool:
    """Check if the user has the required permission"""

    async def _send_reply(content: str) -> None:
        if interaction.response.is_done():
            await interaction.followup.send(content=content, ephemeral=True)
        else:
            await interaction.response.send_message(content=content, ephemeral=True)

    if interaction.guild is None:
        await _send_reply("This command cannot be used outside of a guild.")
        return False

    # Use interaction-scoped permissions to avoid network calls/timeouts.
    has_permission = interaction.user.guild_permissions.is_superset(permission)
    if not has_permission:
        # Instead of f"{permission}", find which permission bit is set
        missing_perms = [name for name, value in permission if value]
        perms_str = ", ".join(missing_perms).replace("_", " ").title()

        await _send_reply(f"You need the `{perms_str}` permission to use this command.")

        return False

    return True


async def require_dev(interaction: nextcord.Interaction) -> bool:
    """Check if the user is the bot developer"""

    if interaction.user.id != config.DEV_ID:
        if interaction.response.is_done():
            await interaction.followup.send(
                content="You do not have permission to use this command.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                content="You do not have permission to use this command.",
                ephemeral=True,
            )
        return False
    return True
