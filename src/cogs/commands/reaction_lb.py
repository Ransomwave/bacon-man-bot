from math import log
from typing import Optional

import nextcord
from nextcord.ext.commands import Cog

import logging
from utils import Logger, checks
import utils

logger = Logger("reaction_lb", "logs/reaction_lb.log", print_level=logging.DEBUG)


class ReactionLeaderboard(Cog):
    def __init__(self, bot: nextcord.Client):
        self.bot = bot

    @nextcord.slash_command(
        name="reaction_lb",
        description="Shows a leaderboard of the most reacted to messages on the selected channel with the specified emoji",
    )
    async def reaction_lb(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            name="channel",
            description="The channel to check reactions in.",
            required=True,
        ),
        emoji: str = nextcord.SlashOption(
            name="emoji",
            description="The emoji to count reactions for.",
            required=True,
        ),
        limit: Optional[int] = nextcord.SlashOption(
            name="limit",
            description="The number of top messages to display (default is 10).",
            required=False,
            max_value=10,
            default=10,
        ),
    ):

        if not checks.require_permission(
            interaction,
            nextcord.Permissions(view_channel=True, read_message_history=True),
        ):
            await interaction.response.send_message(
                "You do not have permission to run this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()  # Defer the response to allow time for processing

        messages = [message async for message in channel.history(limit=None)]

        message_reaction_map = {}

        for message in messages:
            for reaction in message.reactions:
                if str(reaction.emoji) == emoji:
                    logger.debug(
                        f"Message {message.id} has {reaction.count} reactions for emoji '{emoji}'"
                    )
                    message_reaction_map[message] = reaction.count

        sorted_messages = sorted(
            message_reaction_map.items(), key=lambda item: item[1], reverse=True
        )

        sorted_messages = sorted_messages[:limit]  # Get the top `limit` messages

        result_embed = nextcord.Embed(
            title=f"Reaction Leaderboard for {emoji} in {channel.mention}",
            description="Here are the top messages with the most reactions:",
            color=0xFF4747,
        )

        for i, (message, count) in enumerate(sorted_messages[:limit], start=1):
            logger.debug(
                f"Adding message {message.id} with {count} reactions to the leaderboard embed"
            )
            result_embed.add_field(
                name=f"{i}. {message.author.display_name}",
                value=f"{emoji} {count}\n[Message]({message.jump_url})",
                inline=False,
            )

        await interaction.edit_original_message(embed=result_embed)


def setup(bot: nextcord.Client):
    bot.add_cog(ReactionLeaderboard(bot))
