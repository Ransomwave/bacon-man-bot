import aiosqlite

import nextcord
from nextcord.ext.commands import Cog

import bot


# Initializes the starboard SQLite table (obviously)
async def create_starboard_table():
    async with aiosqlite.connect("starboard.db") as db:
        # Create the primary starboard SQL table, if it doesn't exist
        print("Initializing starboard database")
        await db.execute(
            """CREATE TABLE IF NOT EXISTS starboard (
        message_id INTEGER PRIMARY KEY,
        starboard_message_id INTEGER)
        """
        )

        await db.commit()
        print("starboard.db initialized")


class Starboard(Cog):
    def __init__(self, bot):
        self.bot = bot

        # Constants

    SENDING_CHANNEL = 1107624079210582016
    REACT_CHANNELS = [1059899526992904212]
    STAR_EMOJI = "⭐"
    TRIGGER_COUNT = 5
    STRICT_MODE = True  # Toggle strict mode. If it's on, anyone without attachments will be discarded.
    BLACKLIST = []  # Add IDs of people you hate the most.

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.channel_id in self.REACT_CHANNELS:
            return
        if not payload.emoji.name == self.STAR_EMOJI:
            return
        channel = self.bot.get_channel(payload.channel_id)
        message: nextcord.Message = await channel.fetch_message(payload.message_id)

        if message.author in self.BLACKLIST:
            return

        # check message id (check if this thing was already posted)
        value = None
        async with aiosqlite.connect("starboard.db") as db:
            cursor = await db.execute(
                "SELECT * FROM starboard WHERE message_id = ?", (payload.message_id,)
            )
            value = await cursor.fetchone()
            print(f"Fetched value from database: {value}")
        if value:
            return

        reaction = None
        for react in message.reactions:
            if react.emoji == payload.emoji.name:
                reaction = react
                break
        if not reaction or reaction.count < self.TRIGGER_COUNT:
            return

        ctx: nextcord.channel = self.bot.get_channel(self.SENDING_CHANNEL)
        content = message.content
        attachments = []
        jmp = message.jump_url
        if message.attachments != []:
            for attachment in message.attachments:
                f = await attachment.to_file()
                attachments.append(f)
        if message.attachments == [] and self.STRICT_MODE:
            return
        msg = await ctx.send(
            f":star: {reaction.count}/{str(self.TRIGGER_COUNT)}\nby: {message.author.mention}\nin: {jmp}",
            files=attachments,
        )

        # Insert the thing into the database
        async with aiosqlite.connect("starboard.db") as db:
            await db.execute(
                "INSERT INTO starboard (message_id, starboard_message_id) VALUES (?, ?)",
                (message.id, msg.id),
            )
            await db.commit()
            print(
                f"Inserted into database: message_id={message.id}, starboard_message_id={msg.id}"
            )


def setup(bot):
    bot.add_cog(Starboard(bot))
