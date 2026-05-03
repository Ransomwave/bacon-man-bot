import asyncio
import logging
import os

import aiosqlite
import nextcord
from nextcord import emoji
from nextcord.ext.commands import Cog

import config
from utils import checks, db_utils, Logger

logger = Logger("autoreact", "logs/autoreact.log", print_level=logging.DEBUG)


async def setup_db_table():
    await db_utils.create_table(
        "autoreacts",
        {
            "channel_id": "INTEGER PRIMARY KEY",
            "emojis": "TEXT",
        },
    )
    logger.info("Ensured autoreacts table exists in database.")


class Autoreact(Cog):
    def __init__(
        self,
        bot: nextcord.Client,
    ):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        async with aiosqlite.connect(db_utils.config.BOT_DATA_FILE) as db:
            cursor = await db.execute(
                "SELECT emojis FROM autoreacts WHERE channel_id = ?",
                (message.channel.id,),
            )
            row = await cursor.fetchone()
            if not row:
                return

            emojis = await db_utils.string_to_array(row[0])
            for emoji in emojis:
                try:
                    await message.add_reaction(emoji)
                    # await asyncio.sleep(
                    # 0.1
                    # )  # Add a short delay to avoid hitting rate limits
                except Exception as e:
                    logger.exception(
                        f"Failed to add reaction '{emoji}' to message {message.id} in channel {message.channel.id}: {e}"
                    )

    @nextcord.slash_command(
        name="autoreact_add",
        description="Reacts to every message in the specified channel with the registered emojis.",
    )
    async def autoreact_add(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            name="channel",
            description="The channel to react to messages in.",
            required=True,
        ),
        emoji_to_add: str = nextcord.SlashOption(
            name="emoji_to_add",
            description="One or more emojis to react with, separated by commas.",
            required=True,
        ),
    ):
        if not await checks.require_permission(
            interaction, nextcord.Permissions(manage_messages=True)
        ):
            return

        emoji_to_add = [
            emoji.strip() for emoji in emoji_to_add.split(",") if emoji.strip()
        ]

        async with aiosqlite.connect(db_utils.config.BOT_DATA_FILE) as db:
            cursor = await db.execute(
                "SELECT emojis FROM autoreacts WHERE channel_id = ?",
                (channel.id,),
            )
            row = await cursor.fetchone()
            if row:
                existing_emojis = row[0]
                existing_list = await db_utils.string_to_array(existing_emojis)

                # Only add emojis that aren't already in the list
                for emoji in emoji_to_add:
                    if emoji in existing_list:
                        continue
                    existing_list.append(emoji)

                updated_emojis = ",".join(existing_list)
                await db.execute(
                    "UPDATE autoreacts SET emojis = ? WHERE channel_id = ?",
                    (updated_emojis, channel.id),
                )
            else:
                await db.execute(
                    "INSERT INTO autoreacts (channel_id, emojis) VALUES (?, ?)",
                    (channel.id, ",".join(emoji_to_add)),
                )
            await db.commit()

        logger.info(
            f"Registered autoreactions for channel {channel.id} with emojis: {', '.join(emoji_to_add)}"
        )
        await interaction.response.send_message(
            f"Success! I will react to new messages sent in <#{channel.id}> with {', '.join(emoji_to_add)}.",
            ephemeral=True,
        )

    @nextcord.slash_command(
        name="autoreact_remove",
        description="Removes a specific emoji reaction when reacting to a message in the specified channel.",
    )
    async def autoreact_remove(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            name="channel",
            description="The channel to remove reactions from.",
            required=True,
        ),
        emoji_to_remove: str = nextcord.SlashOption(
            name="emoji_to_remove",
            description="The emoji to remove as a reaction.",
            required=True,
        ),
    ):
        if not await checks.require_permission(
            interaction, nextcord.Permissions(manage_messages=True)
        ):
            return

        emoji_to_remove = emoji_to_remove.strip()

        async with aiosqlite.connect(db_utils.config.BOT_DATA_FILE) as db:
            cursor = await db.execute(
                "SELECT emojis FROM autoreacts WHERE channel_id = ?",
                (channel.id,),
            )
            row = await cursor.fetchone()
            if row:
                existing_emojis = row[0]
                updated_emojis = await db_utils.remove_from_array_string(
                    existing_emojis, emoji_to_remove
                )
                await db.execute(
                    "UPDATE autoreacts SET emojis = ? WHERE channel_id = ?",
                    (updated_emojis, channel.id),
                )
                await db.commit()

        await interaction.response.send_message(
            f"Success! I will no longer react to new messages sent in <#{channel.id}> with {emoji_to_remove}.",
            ephemeral=True,
        )

    @nextcord.slash_command(
        name="autoreact_deregister",
        description="Completely stops reacting to messages in the specified channel.",
    )
    async def autoreact_deregister(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            name="channel",
            description="The channel to deregister reactions from.",
            required=True,
        ),
    ):
        if not await checks.require_permission(
            interaction, nextcord.Permissions(manage_messages=True)
        ):
            return

        async with aiosqlite.connect(db_utils.config.BOT_DATA_FILE) as db:
            await db.execute(
                "DELETE FROM autoreacts WHERE channel_id = ?",
                (channel.id,),
            )
            await db.commit()

        await interaction.response.send_message(
            f"Success! I will no longer react to new messages sent in <#{channel.id}>.",
            ephemeral=True,
        )

    @nextcord.slash_command(
        name="autoreact_list",
        description="Lists the registered autoreactions for a specified channel.",
    )
    async def autoreact_list(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            name="channel",
            description="The channel to list autoreactions for.",
            required=False,
        ),
    ):
        if not await checks.require_permission(
            interaction, nextcord.Permissions(manage_messages=True)
        ):
            return

        await interaction.response.defer(ephemeral=True)

        async with aiosqlite.connect(config.BOT_DATA_FILE) as db:
            if channel:
                cursor = await db.execute(
                    "SELECT emojis FROM autoreacts WHERE channel_id = ?",
                    (channel.id,),
                )
                row = await cursor.fetchone()
                if row:
                    emojis = row[0]
                    await interaction.edit_original_message(
                        content=f"Autoreactions for <#{channel.id}>: {emojis}"
                    )
                else:
                    await interaction.edit_original_message(
                        content=f"No autoreactions registered for <#{channel.id}>."
                    )
            else:
                cursor = await db.execute("SELECT channel_id, emojis FROM autoreacts")
                rows = await cursor.fetchall()
                logger.debug(f"Fetched autoreacts from database: {rows}")
                if rows:
                    message = "Registered autoreactions:\n"
                    for row in rows:
                        message += f"<#{row[0]}>: {row[1]}\n"
                    await interaction.edit_original_message(content=message)
                else:
                    await interaction.edit_original_message(
                        content="No autoreactions registered."
                    )


def setup(bot: nextcord.Client):
    bot.add_cog(Autoreact(bot))
