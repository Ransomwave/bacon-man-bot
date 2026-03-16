from typing import Optional, Union

import aiosqlite
import nextcord
from nextcord.ext.commands import Cog

import config
from utils import checks

ChannelType = Union[nextcord.TextChannel, nextcord.Thread]
DEFAULT_TITLE = "Reaction Roles"
DEFAULT_DESCRIPTION = "React to get a role."


def _build_panel_embed(title: str, description: str, rows: list[tuple[str, int]]):
    roles_text = (
        "No reaction roles configured yet. Use `/reaction_role_add` to add one."
        if not rows
        else "\n".join([f"{emoji} — <@&{role_id}>" for emoji, role_id in rows])
    )

    body = description.strip()
    if body:
        body = f"{body}\n\n{roles_text}"
    else:
        body = roles_text

    return nextcord.Embed(title=title, description=body, color=0xFF4747)


async def _table_exists(db: aiosqlite.Connection, table_name: str) -> bool:
    cursor = await db.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return await cursor.fetchone() is not None


async def _migrate_legacy_schema(db: aiosqlite.Connection):
    has_old_roles = await _table_exists(db, "reaction_roles")
    has_old_message = await _table_exists(db, "reaction_roles_message")
    if not (has_old_roles and has_old_message):
        return

    cursor = await db.execute("SELECT message_id FROM reaction_roles_message LIMIT 1")
    legacy_message = await cursor.fetchone()
    if legacy_message is None:
        return

    legacy_message_id = legacy_message[0]
    await db.execute(
        """
        INSERT OR IGNORE INTO reaction_role_messages (message_id, channel_id, title, description)
        VALUES (?, ?, ?, ?)
        """,
        (
            legacy_message_id,
            int(config.REACTION_ROLES_CHANNEL),
            DEFAULT_TITLE,
            DEFAULT_DESCRIPTION,
        ),
    )

    cursor = await db.execute("SELECT emoji, role_id FROM reaction_roles")
    legacy_rows = await cursor.fetchall()
    for emoji, role_id in legacy_rows:
        await db.execute(
            """
            INSERT OR IGNORE INTO reaction_role_entries (message_id, emoji, role_id)
            VALUES (?, ?, ?)
            """,
            (legacy_message_id, emoji, role_id),
        )


async def create_reaction_roles_table():
    async with aiosqlite.connect("bot_data.db") as db:
        print("Initializing reaction roles database")
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reaction_role_messages (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reaction_role_entries (
                message_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (message_id, emoji),
                FOREIGN KEY (message_id) REFERENCES reaction_role_messages (message_id)
                    ON DELETE CASCADE
            )
            """
        )

        await _migrate_legacy_schema(db)
        await db.commit()
        print("bot_data.db (reaction roles) initialized")


async def add_reactions_to_message(message: nextcord.Message, emojis: list[str]):
    current_emojis = [str(r.emoji) for r in message.reactions]
    to_remove = [r for r in message.reactions if str(r.emoji) not in emojis]
    to_add = [e for e in emojis if e not in current_emojis]

    for reaction in to_remove:
        try:
            await message.clear_reaction(reaction.emoji)
        except nextcord.HTTPException as e:
            print(
                f"Failed to remove reaction {reaction.emoji} from reaction roles message: {e}"
            )

    for emoji in to_add:
        try:
            await message.add_reaction(emoji)
        except nextcord.HTTPException as e:
            print(f"Failed to add reaction {emoji} to reaction roles message: {e}")


class ReactionRolesCommands(Cog):
    def __init__(self, bot: nextcord.Client):
        self.bot = bot
        self.channel: Optional[ChannelType] = getattr(
            bot, "reaction_roles_channel", None
        )

    async def get_channel(self) -> Optional[ChannelType]:
        if self.channel is not None:
            return self.channel

        try:
            channel_id = int(config.REACTION_ROLES_CHANNEL)
        except (TypeError, ValueError):
            self.bot.logger.error("Invalid REACTION_ROLES_CHANNEL config value.")
            return None

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (nextcord.NotFound, nextcord.Forbidden, nextcord.HTTPException) as e:
                self.bot.logger.error(f"Failed to fetch reaction roles channel: {e}")
                return None

        if not isinstance(channel, (nextcord.TextChannel, nextcord.Thread)):
            self.bot.logger.error(
                f"REACTION_ROLES_CHANNEL ({channel_id}) is not a text channel/thread."
            )
            return None

        self.channel = channel
        setattr(self.bot, "reaction_roles_channel", channel)
        return channel

    async def _get_channel_by_id(self, channel_id: int) -> Optional[ChannelType]:
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (nextcord.NotFound, nextcord.Forbidden, nextcord.HTTPException):
                return None

        if isinstance(channel, (nextcord.TextChannel, nextcord.Thread)):
            return channel

        return None

    @staticmethod
    def _parse_message_id(raw_message_id: str) -> Optional[int]:
        value = raw_message_id.strip()
        if not value.isdigit():
            return None
        return int(value)

    async def _refresh_panel_message(self, message_id: int):
        async with aiosqlite.connect("bot_data.db") as db:
            await db.execute("PRAGMA foreign_keys = ON")

            cursor = await db.execute(
                """
                SELECT channel_id, title, description
                FROM reaction_role_messages
                WHERE message_id = ?
                """,
                (message_id,),
            )
            panel = await cursor.fetchone()
            if panel is None:
                raise RuntimeError(f"Reaction role panel {message_id} does not exist.")

            channel_id, title, description = panel
            cursor = await db.execute(
                """
                SELECT emoji, role_id
                FROM reaction_role_entries
                WHERE message_id = ?
                ORDER BY emoji
                """,
                (message_id,),
            )
            rows = await cursor.fetchall()

        channel = await self._get_channel_by_id(channel_id)
        if channel is None:
            raise RuntimeError(
                f"Could not access channel {channel_id} for reaction role panel {message_id}."
            )

        try:
            message = await channel.fetch_message(message_id)
        except nextcord.NotFound:
            async with aiosqlite.connect("bot_data.db") as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute(
                    "DELETE FROM reaction_role_messages WHERE message_id = ?",
                    (message_id,),
                )
                await db.commit()
            raise RuntimeError(
                f"Panel message {message_id} no longer exists. Removed it from the database."
            )

        embed = _build_panel_embed(title, description, rows)
        await message.edit(embed=embed, content=None)
        await add_reactions_to_message(message, [emoji for emoji, _ in rows])

    @nextcord.slash_command(
        name="reaction_role_message_create",
        description="Create a new reaction role panel message",
    )
    async def reaction_role_message_create(
        self,
        interaction: nextcord.Interaction,
        title: str = nextcord.SlashOption(
            name="title",
            description="Panel title",
            required=True,
        ),
        description: str = nextcord.SlashOption(
            name="description",
            description="Panel description",
            required=True,
        ),
    ):
        if not await checks.require_permission(interaction, "administrator"):
            return

        await interaction.response.defer(ephemeral=True)
        channel = await self.get_channel()
        if channel is None:
            await interaction.edit_original_message(
                content="Could not find the reaction roles channel configured in REACTION_ROLES_CHANNEL."
            )
            return

        message = await channel.send(embed=_build_panel_embed(title, description, []))
        async with aiosqlite.connect("bot_data.db") as db:
            await db.execute(
                """
                INSERT INTO reaction_role_messages (message_id, channel_id, title, description)
                VALUES (?, ?, ?, ?)
                """,
                (message.id, channel.id, title, description),
            )
            await db.commit()

        await interaction.edit_original_message(
            content=(
                f"Created reaction role panel with message ID `{message.id}`. "
                "Use `/reaction_role_add` to attach roles to it."
            )
        )

    @nextcord.slash_command(
        name="reaction_role_message_edit",
        description="Edit title/description for a reaction role panel",
    )
    async def reaction_role_message_edit(
        self,
        interaction: nextcord.Interaction,
        message_id: str = nextcord.SlashOption(
            name="message_id",
            description="Panel message ID (copy from Discord message)",
            required=True,
        ),
        title: Optional[str] = nextcord.SlashOption(
            name="title",
            description="New panel title",
            required=False,
        ),
        description: Optional[str] = nextcord.SlashOption(
            name="description",
            description="New panel description",
            required=False,
        ),
    ):
        if not await checks.require_permission(interaction, "administrator"):
            return

        if title is None and description is None:
            await interaction.response.send_message(
                "Provide at least one value: title or description.", ephemeral=True
            )
            return

        parsed_message_id = self._parse_message_id(message_id)
        if parsed_message_id is None:
            await interaction.response.send_message(
                "message_id must be a numeric Discord message ID.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        async with aiosqlite.connect("bot_data.db") as db:
            cursor = await db.execute(
                """
                SELECT title, description
                FROM reaction_role_messages
                WHERE message_id = ?
                """,
                (parsed_message_id,),
            )
            panel = await cursor.fetchone()
            if panel is None:
                await interaction.edit_original_message(
                    content=(
                        f"No reaction role panel found for message ID {parsed_message_id}."
                    )
                )
                return

            new_title = title if title is not None else panel[0]
            new_description = description if description is not None else panel[1]

            await db.execute(
                """
                UPDATE reaction_role_messages
                SET title = ?, description = ?
                WHERE message_id = ?
                """,
                (new_title, new_description, parsed_message_id),
            )
            await db.commit()

        try:
            await self._refresh_panel_message(parsed_message_id)
        except Exception as e:
            self.bot.logger.error(f"Failed to refresh panel {parsed_message_id}: {e}")
            await interaction.edit_original_message(content=f"Error: {e}")
            return

        await interaction.edit_original_message(
            content=f"Updated panel {parsed_message_id}."
        )

    @nextcord.slash_command(
        name="reaction_role_add", description="Add/update a reaction role in a panel"
    )
    async def reaction_role_add(
        self,
        interaction: nextcord.Interaction,
        message_id: str = nextcord.SlashOption(
            name="message_id",
            description="Panel message ID (copy from Discord message)",
            required=True,
        ),
        emoji: str = nextcord.SlashOption(
            name="emoji",
            description="The emoji for the reaction role",
            required=True,
        ),
        role: nextcord.Role = nextcord.SlashOption(
            name="role",
            description="The role to assign for the reaction role",
            required=True,
        ),
    ):
        if not await checks.require_permission(interaction, "administrator"):
            return

        parsed_message_id = self._parse_message_id(message_id)
        if parsed_message_id is None:
            await interaction.response.send_message(
                "message_id must be a numeric Discord message ID.", ephemeral=True
            )
            return

        emoji = str(emoji).strip()

        await interaction.response.defer(ephemeral=True)

        async with aiosqlite.connect("bot_data.db") as db:
            cursor = await db.execute(
                "SELECT 1 FROM reaction_role_messages WHERE message_id = ?",
                (parsed_message_id,),
            )
            panel_exists = await cursor.fetchone() is not None
            if not panel_exists:
                await interaction.edit_original_message(
                    content=(
                        f"No reaction role panel found for message ID {parsed_message_id}."
                    )
                )
                return

            try:
                await db.execute(
                    """
                    INSERT INTO reaction_role_entries (message_id, emoji, role_id)
                    VALUES (?, ?, ?)
                    ON CONFLICT(message_id, emoji) DO UPDATE SET role_id = excluded.role_id
                    """,
                    (parsed_message_id, emoji, role.id),
                )
                await db.commit()
            except aiosqlite.Error as e:
                self.bot.logger.error(f"Error adding reaction role: {e}")
                await interaction.edit_original_message(content=f"Error: {e}")
                return

        try:
            await self._refresh_panel_message(parsed_message_id)
        except Exception as e:
            self.bot.logger.error(f"Error updating reaction role panel: {e}")
            await interaction.edit_original_message(content=f"Error: {e}")
            return

        await interaction.edit_original_message(
            content=(
                f"Added/updated role mapping on panel {parsed_message_id}: {emoji} -> {role.name}"
            )
        )

    @nextcord.slash_command(
        name="reaction_role_remove", description="Remove a reaction role by emoji"
    )
    async def reaction_role_remove(
        self,
        interaction: nextcord.Interaction,
        message_id: str = nextcord.SlashOption(
            name="message_id",
            description="Panel message ID (copy from Discord message)",
            required=True,
        ),
        emoji: str = nextcord.SlashOption(
            name="emoji",
            description="The emoji mapping to remove",
            required=True,
        ),
    ):
        if not await checks.require_permission(interaction, "administrator"):
            return

        parsed_message_id = self._parse_message_id(message_id)
        if parsed_message_id is None:
            await interaction.response.send_message(
                "message_id must be a numeric Discord message ID.", ephemeral=True
            )
            return

        emoji = str(emoji).strip()
        await interaction.response.defer(ephemeral=True)

        async with aiosqlite.connect("bot_data.db") as db:
            try:
                cursor = await db.execute(
                    """
                    DELETE FROM reaction_role_entries
                    WHERE message_id = ? AND emoji = ?
                    """,
                    (parsed_message_id, emoji),
                )
                await db.commit()
            except aiosqlite.Error as e:
                self.bot.logger.error(f"Error removing reaction role: {e}")
                await interaction.edit_original_message(content=f"Error: {e}")
                return

            if cursor.rowcount == 0:
                await interaction.edit_original_message(
                    content=(
                        f"No mapping found for emoji {emoji} on panel {parsed_message_id}."
                    )
                )
                return

        try:
            await self._refresh_panel_message(parsed_message_id)
        except Exception as e:
            self.bot.logger.error(f"Error updating reaction role panel: {e}")
            await interaction.edit_original_message(content=f"Error: {e}")
            return

        await interaction.edit_original_message(
            content=f"Removed mapping on panel {parsed_message_id}: {emoji}"
        )

    @nextcord.slash_command(
        name="reaction_role_list", description="List reaction role panels or mappings"
    )
    async def reaction_role_list(
        self,
        interaction: nextcord.Interaction,
        message_id: Optional[str] = nextcord.SlashOption(
            name="message_id",
            description="Panel message ID (optional)",
            required=False,
        ),
    ):
        if not await checks.require_permission(interaction, "administrator"):
            return

        async with aiosqlite.connect("bot_data.db") as db:
            if message_id is None:
                cursor = await db.execute(
                    """
                    SELECT m.message_id, m.title, COUNT(e.emoji)
                    FROM reaction_role_messages m
                    LEFT JOIN reaction_role_entries e ON e.message_id = m.message_id
                    GROUP BY m.message_id, m.title
                    ORDER BY m.message_id
                    """
                )
                panels = await cursor.fetchall()

                if not panels:
                    await interaction.response.send_message(
                        "No reaction role panels found. Use `/reaction_role_message_create` first.",
                        ephemeral=True,
                    )
                    return

                description = "\n".join(
                    [
                        f"{panel_id} | {title} | {count} mappings"
                        for panel_id, title, count in panels
                    ]
                )
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="Reaction Role Panels",
                        description=description,
                        color=0xFF4747,
                    ),
                    ephemeral=True,
                )
                return

            parsed_message_id = self._parse_message_id(message_id)
            if parsed_message_id is None:
                await interaction.response.send_message(
                    "message_id must be a numeric Discord message ID.", ephemeral=True
                )
                return

            cursor = await db.execute(
                "SELECT title FROM reaction_role_messages WHERE message_id = ?",
                (parsed_message_id,),
            )
            panel = await cursor.fetchone()
            if panel is None:
                await interaction.response.send_message(
                    f"No reaction role panel found for message ID {parsed_message_id}.",
                    ephemeral=True,
                )
                return

            cursor = await db.execute(
                """
                SELECT emoji, role_id
                FROM reaction_role_entries
                WHERE message_id = ?
                ORDER BY emoji
                """,
                (parsed_message_id,),
            )
            rows = await cursor.fetchall()

        if not rows:
            await interaction.response.send_message(
                f"Panel {parsed_message_id} ({panel[0]}) has no mappings yet.",
                ephemeral=True,
            )
            return

        description = "\n".join(
            [f"{emoji} -> <@&{role_id}>" for emoji, role_id in rows]
        )
        await interaction.response.send_message(
            embed=nextcord.Embed(
                title=f"Panel {parsed_message_id} ({panel[0]})",
                description=description,
                color=0xFF4747,
            ),
            ephemeral=True,
        )

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        if payload.member and payload.member.bot:
            return

        async with aiosqlite.connect("bot_data.db") as db:
            cursor = await db.execute(
                """
                SELECT role_id
                FROM reaction_role_entries
                WHERE message_id = ? AND emoji = ?
                """,
                (payload.message_id, str(payload.emoji)),
            )
            result = await cursor.fetchone()

        if result is None:
            return

        role_id = result[0]
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            self.bot.logger.error(
                f"Guild with ID {payload.guild_id} not found for reaction role assignment."
            )
            return

        role = guild.get_role(role_id)
        if role is None:
            self.bot.logger.error(
                f"Role with ID {role_id} not found in guild {payload.guild_id} for reaction role assignment."
            )
            return

        member = payload.member
        if member is None:
            member = guild.get_member(payload.user_id)
            if member is None:
                return

        try:
            await member.add_roles(role, reason="Reaction role added")
        except nextcord.Forbidden:
            self.bot.logger.error(
                f"Missing permissions to add role {role.name} to user {member}."
            )

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: nextcord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        async with aiosqlite.connect("bot_data.db") as db:
            cursor = await db.execute(
                """
                SELECT role_id
                FROM reaction_role_entries
                WHERE message_id = ? AND emoji = ?
                """,
                (payload.message_id, str(payload.emoji)),
            )
            result = await cursor.fetchone()

        if result is None:
            return

        role_id = result[0]
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            self.bot.logger.error(
                f"Guild with ID {payload.guild_id} not found for reaction role removal."
            )
            return

        role = guild.get_role(role_id)
        if role is None:
            self.bot.logger.error(
                f"Role with ID {role_id} not found in guild {payload.guild_id} for reaction role removal."
            )
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            self.bot.logger.error(
                f"Member with ID {payload.user_id} not found in guild {payload.guild_id} for reaction role removal."
            )
            return

        try:
            await member.remove_roles(role, reason="Reaction role removed")
        except nextcord.Forbidden:
            self.bot.logger.error(
                f"Missing permissions to remove role {role.name} from user {member}."
            )


def setup(bot: nextcord.Client):
    bot.add_cog(ReactionRolesCommands(bot))
