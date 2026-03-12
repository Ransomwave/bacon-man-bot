import nextcord
from nextcord.ext.commands import Cog

import config
from utils import thread_utils


class OnBugReportThreadCreate(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_thread_create(self, thread: nextcord.Thread):
        # Check if the thread belongs to the target forum channel
        if thread.parent_id != config.BUG_REPORT_CHANNEL:
            return

        try:
            # Ensure the thread has started before interacting
            await thread.join()

            # Send a custom reply message to the thread author
            author_mention = thread.owner.mention if thread.owner else "Unknown"
            await thread.send(
                f"### Hi {author_mention}, thanks for reaching out! I appreciate you took time to report a bug in one of my games.\n"
                f"* Don't ping the dev! Keep in mind <@{config.DEV_ID}> might need up to 1 day to respond.\n"
                f"* Make sure to **provide a screenshot of the Roblox Developer Console** if you haven't already. Bring it up by pressing F9 or typing `/console` in chat (if available).\n"
                f"* Review the guidelines and **provide any additional details that could help me resolve the issue.** (Photos, Videos, What you were doing before, etc.)\n"
                f"Thank you for your patience & understanding!\n"
                f"-# This is an automated response, I am a bot."
            )

            await thread_utils.apply_tag(thread, config.BUG_REPORT_TAGS["Open"])

            print(f"Replied to thread in bug-report: {thread.name}")

        except Exception as e:
            print(f'Failed to reply to thread in bug-report: "{thread.name}": {e}')


def setup(bot):
    bot.add_cog(OnBugReportThreadCreate(bot))
