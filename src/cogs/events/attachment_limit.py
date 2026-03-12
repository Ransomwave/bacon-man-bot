import re as regex

import nextcord
from nextcord.ext import tasks
from nextcord.ext.commands import Cog

from datetime import datetime, timedelta

import config


class AttachmentLimit(Cog):

    YES_EMOJI = "<:Yes:1097495643204882442>"
    NO_EMOJI = "<:No:1097495733780873358>"

    WHITELISTED_CHANNELS = [
        995400838849769509,
        1059899526992904212,
        1076248681386352760,
        1074713502205358121,
    ]

    WHITELISTED_USERS = [config.DEV_ID]

    # Define the global attachment limit and cooldown duration
    IMAGE_LIMIT = 10
    COOLDOWN_DURATION = 60
    # Dictionary to track image uploads per server
    image_uploads = {}

    def __init__(self, client):
        self.client = client

    # Background task to clear image counts every 1 minute
    @tasks.loop(seconds=60)
    async def clear_image_counts(self):
        current_time = datetime.now()
        for server_id, data in list(self.image_uploads.items()):
            last_timestamp = data["timestamp"]
            if current_time - last_timestamp >= timedelta(seconds=60):
                del self.image_uploads[server_id]

    @clear_image_counts.before_loop
    async def before_clear_image_counts(self):
        await self.client.wait_until_ready()

    @Cog.listener()
    async def on_message(self, message: nextcord.Message):

        client = self.client

        if message.author.bot:
            return

        # Check if the message is in #suggestions
        if (
            message.channel.id == 995400838849769505
            or message.channel.id == 1237050991711359047
        ):
            # If it is, add voting reactions to the message
            try:
                # print("Vote reactions sent in proper channels.")
                await message.add_reaction(self.YES_EMOJI)
                await message.add_reaction(self.NO_EMOJI)
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            # Check if the message is in any of the whitelisted channels by their IDs
            # The channels are: media, fan-art, other-art, your-creations
            if message.channel.id in self.WHITELISTED_CHANNELS:
                await client.process_commands(message)
                return

            if message.attachments or regex.search(
                r"(https?:\/\/(?:[\w-]+\.)?(tenor|giphy|klipy|youtube)\.com\/\S+|https?:\/\/\S+\.(?:gif|gifv|jpe?g|png|apng|webp|mp4|mp3|wav|ogg|txt)(?:\?\S+)?)",
                message.content,
            ):

                server_id = message.guild.id

                # Check if the user is whitelisted (their messages won't be deleted)
                if message.author.id in self.WHITELISTED_USERS:
                    await client.process_commands(message)
                    return

                # Initialize or update the image count for the server
                if server_id not in self.image_uploads:
                    self.image_uploads[server_id] = {
                        "count": 1,
                        "timestamp": datetime.now(),
                    }
                else:
                    current_time = datetime.now()
                    last_timestamp = self.image_uploads[server_id]["timestamp"]

                    # Check if the cooldown has passed
                    if current_time - last_timestamp >= timedelta(
                        seconds=self.COOLDOWN_DURATION
                    ):
                        self.image_uploads[server_id] = {
                            "count": 1,
                            "timestamp": current_time,
                        }
                    else:
                        self.image_uploads[server_id]["count"] += 1
                        self.image_uploads[server_id]["timestamp"] = current_time

                    # Check if the server has exceeded the image limit
                    if self.image_uploads[server_id]["count"] > self.IMAGE_LIMIT:
                        await message.delete()
                        await message.channel.send(
                            f"Slow down, {message.author.mention}. The server has reached the attachment limit ({self.IMAGE_LIMIT} attachments/{self.COOLDOWN_DURATION} seconds). Try again later!\n-# Someone's spamming? Ping the staff team!",
                            delete_after=5,
                        )
                        return

        await client.process_commands(message)


def setup(bot):
    bot.add_cog(AttachmentLimit(bot))
