# Allows users to create media channels where only messages containing media attachments (images, videos, etc.) are allowed.
# Non-media messages will be automatically deleted.

import logging

import aiosqlite

import config
from utils import db_utils, Logger
import nextcord
from nextcord.ext.commands import Cog


async def setup_db_table():
    await db_utils.create_table(
        "media_channels",
        {
            "channel_id": "INTEGER PRIMARY KEY",
        },
    )


logger = Logger("mediachannel", "logs/mediachannel.log", print_level=logging.DEBUG)


class MediaChannel(Cog):
    def __init__(self, bot: nextcord.Client):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if (
            message.author.bot
            or message.attachments
            or message.author.guild_permissions.administrator
        ):
            return

        async with aiosqlite.connect(db_utils.config.BOT_DATA_FILE) as db:
            cursor = await db.execute(
                "SELECT channel_id FROM media_channels WHERE channel_id = ?",
                (message.channel.id,),
            )
            row = await cursor.fetchone()
            if not row:
                return

            if not message.attachments:
                try:
                    await message.delete()
                    await message.channel.send(
                        f"{message.author.mention}, this channel is for media only. Your message has been deleted.",
                        delete_after=5,
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to delete non-media message {message.id} in media channel {message.channel.id}: {e}"
                    )

    @nextcord.slash_command(
        name="mediachannel_add",
        description="Register a channelas 'media only', where only messages containing media attachments are allowed. Non-media messages will be automatically deleted.",
    )
    async def mediachannel_add(self, interaction: nextcord.Interaction):
        async with aiosqlite.connect(db_utils.config.BOT_DATA_FILE) as db:
            await db.execute(
                "INSERT OR IGNORE INTO media_channels (channel_id) VALUES (?)",
                (interaction.channel_id,),
            )
            await db.commit()

        await interaction.response.send_message(
            f"Channel <#{interaction.channel_id}> has been registered as a media channel.",
            ephemeral=True,
        ),

    @nextcord.slash_command(
        name="mediachannel_remove",
        description="Unregister a channel as 'media only'. Messages without media attachments will no longer be deleted.",
    )
    async def mediachannel_remove(self, interaction: nextcord.Interaction):
        async with aiosqlite.connect(db_utils.config.BOT_DATA_FILE) as db:
            await db.execute(
                "DELETE FROM media_channels WHERE channel_id = ?",
                (interaction.channel_id,),
            )
            await db.commit()

        await interaction.response.send_message(
            f"Channel <#{interaction.channel_id}> has been unregistered as a media channel.",
            ephemeral=True,
        )

    @nextcord.slash_command(
        name="mediachannel_list",
        description="List all registered media channels.",
    )
    async def mediachannel_list(self, interaction: nextcord.Interaction):
        async with aiosqlite.connect(db_utils.config.BOT_DATA_FILE) as db:
            cursor = await db.execute("SELECT channel_id FROM media_channels")
            rows = await cursor.fetchall()

        if not rows:
            await interaction.response.send_message(
                "No media channels registered.", ephemeral=True
            )
            return

        channel_mentions = [f"<#{row[0]}>" for row in rows]
        await interaction.response.send_message(
            "Registered media channels:\n" + "\n".join(channel_mentions), ephemeral=True
        )


def setup(bot: nextcord.Client):
    bot.add_cog(MediaChannel(bot))
