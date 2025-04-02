import nextcord as nextcord
from nextcord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta  # Import the datetime module
import asyncio, aiosqlite
import re

import platform
import os
from dotenv import load_dotenv
load_dotenv(override=True)


#discord
client : commands.Bot = commands.Bot(command_prefix = 'b!', intents = nextcord.Intents.all())

##
url = "https://www.roblox.com/games/8197423034/get-a-drink-at-3-am-beta"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
##

## constants
OWNER_ID=777460173115097098

# Constants for the forum channels
# Forum channel ID where the bot should reply
BUG_REPORT_CHANNEL = 1283902220630491178

TAGS = {
    "Open" : 1283903449897111674,
    "Fixed" : 1283903640989470750,
    "AlreadyFixed" : 1325897239905964083,
    "NotBug" : 1283903556927361075,
}

async def apply_tag_to_thread(thread, tag_id):
    # Fetch the forum channel that owns this thread
    forum_channel = thread.parent

    # Find the tag by its ID
    tagToApply = nextcord.utils.get(forum_channel.available_tags, id=tag_id)

    if tagToApply is None:
        print(f"Tag with ID {tag_id} not found by nextcord.")
    else:
        applied_tags = thread.applied_tags
        applied_tags.append(tagToApply)  # Append the tag object, not an integer
        print(f"Applied tags: {applied_tags}")

        # Apply the updated tags to the thread
        await thread.edit(applied_tags=applied_tags)

# Initializes the starboard SQLite table (obviously)
async def _create_starboard_table(): 
    async with aiosqlite.connect("starboard.db") as db:
        # Create the primary starboard SQL table, if it doesn't exist
        print("Initializing starboard database")
        await db.execute('''CREATE TABLE IF NOT EXISTS starboard (
        message_id INTEGER PRIMARY KEY,
        starboard_message_id INTEGER)
        ''')
        
        await db.commit()
        print("starboard.db initialized")

@client.event
async def on_command_error(ctx, exp : Exception): 
    if exp == commands.MissingPermissions:
        await ctx.send("Error: Missing permissions.")
    else:
        raise exp

@client.event
async def on_ready():
    activity = nextcord.Activity(type=nextcord.ActivityType.watching, name="Ransomwave's Games")
    await client.change_presence(status=nextcord.Status.online, activity=activity)
    await _create_starboard_table()
    print('=============== RUNNING ===============')

@client.slash_command(name="ping", description="Get the bot's latency.")
async def ping(ctx):
    latency = client.latency * 1000
    embed = nextcord.Embed(colour=nextcord.Colour.red())
    embed.add_field(name="Client Latency", value=f"Ping value: **{latency}ms**")
    await ctx.send(embed=embed)

@client.slash_command(name="whoishosting", description="(DEV ONLY) Get the hostname of the machine running the bot.")
async def whoishosting(interaction: nextcord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("You are not authorized to execute this command.",ephemeral=True)
        return
    
    uname = platform.uname()
    embed = nextcord.Embed(colour=nextcord.Colour.red())
    embed.add_field(name="System Information", value=f"Release: **{uname.system} {uname.version}**")
    embed.add_field(name="Architecture", value=f"Host: **{uname.machine}**")

    await interaction.response.send_message(embed=embed,ephemeral=True)

@client.slash_command(name="stats", description="Get a game's stats", guild_ids=[995400838136746154])
async def stats(interaction: nextcord.Interaction, id: int = 8197423034):
    url = f"https://www.roblox.com/games/{id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    game_name = soup.find('h1', class_='game-name').text.strip()
    universeIdUrl = f'https://apis.roblox.com/universes/v1/places/{id}/universe'
    
    universeJSON = requests.get(universeIdUrl)
    universeJSON = universeJSON.json()
    universeID = universeJSON['universeId']

    playersUrl = f'https://games.roblox.com/v1/games?universeIds={universeID}'
    
    response = requests.get(playersUrl)
    response = response.json()
    response = response.get('data')[0]

    
    playing = response['playing']
    visits = response['visits']
    favourites = response['favoritedCount']
    creator = response['creator']['name']
    # favourites = "{:,}".format(response['favoritedCount'])
    # favourites = f"{int(response['favoritedCount']):,}"
    
    iconUrl = f'https://thumbnails.roblox.com/v1/games/icons?universeIds={universeID}&size=150x150&format=Png&isCircular=false'
    iconRequest = requests.get(iconUrl)
    iconJSON = iconRequest.json()
    icon = iconJSON['data'][0]['imageUrl']

    embed = nextcord.Embed(title="Game Stats:", description=f"{game_name} ({id})", color=0xff4747)
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Creator:", value=creator, inline=False)
    embed.add_field(name="Concurrent Players:", value=playing, inline=True)
    embed.add_field(name="Visit Count:", value=visits, inline=True)
    embed.add_field(name="Favorite Count:", value=favourites, inline=False)
    embed.add_field(name="Universe ID:", value=universeID, inline=False)

    await interaction.response.send_message(embed=embed)

@client.slash_command(description="Show available commands and their usage")
async def help(ctx):
    embed = nextcord.Embed(title="Command List", color=0xff4747)
    
    # Ping Command
    ping_description = "Get the bot's latency."
    ping_usage = "/ping"
    embed.add_field(name="/ping", value=f"Description: {ping_description}\nUsage: `{ping_usage}`", inline=False)
    
    # Stats Command
    stats_description = "Get a game's stats."
    stats_usage = "/stats [id (leave blank for gada3 stats)]"
    embed.add_field(name="/stats", value=f"Description: {stats_description}\nUsage: `{stats_usage}`", inline=False)

    embed.add_field(name="Client Events", value="This bot has a few Client Events\n- Add vote reactions to all messages in a channel.\n- Limit media every 60 seconds to prevent attachment spam.\n- Starboard functionality in art channels\nMore Roblox-related functionality will be added in the future!", inline=False)

    embed.set_footer(text="Made with ❤️ by Ransomwave")
    
    await ctx.send(embed=embed)


# Define the global image limit and cooldown duration
IMAGE_LIMIT = 15
COOLDOWN_DURATION = 60  # 60 seconds
# Dictionary to track image uploads per server
image_uploads = {}
# Whitelisted user IDs (add any user IDs you want to whitelist)
whitelisted_users = [777460173115097098]
@client.event
async def on_message(message: nextcord.Message):
    if message.author.bot:
        return

    # Check if the message is in #suggestions
    if message.channel.id == 995400838849769505 or message.channel.id == 1237050991711359047:
        # If it is, add voting reactions to the message
        try:
            # print("Vote reactions sent in proper channels.")
            await message.add_reaction('<:Yes:1097495643204882442>')
            await message.add_reaction('<:No:1097495733780873358>')
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        # Check if the message is in any of the whitelisted channels by their IDs
        # The channels are: media, suggestions, bug-report, fan-art, other-art, arg-discussion
        whitelisted_channels = [995400838849769509, 995400838849769505, 995422771628757022, 1059899526992904212, 1076248681386352760, 1074713502205358121, 1143688301841231882]
        if message.channel.id in whitelisted_channels:
            await client.process_commands(message)
            return

        if message.attachments or re.search(r'(https?://(?:www\.)?tenor\.com/.+|https?://(?:www\.)?giphy\.com/.+|https?://\S+\.(gif|gifv|jpg|jpeg|png|apng|webp|mp4|mp3|wav|ogg|txt))', message.content):

            server_id = message.guild.id

            # Check if the user is whitelisted (their messages won't be deleted)
            if message.author.id in whitelisted_users:
                await client.process_commands(message)
                return

            # Initialize or update the image count for the server
            if server_id not in image_uploads:
                image_uploads[server_id] = {"count": 1, "timestamp": datetime.now()}
            else:
                current_time = datetime.now()
                last_timestamp = image_uploads[server_id]["timestamp"]

                # Check if the cooldown has passed
                if current_time - last_timestamp >= timedelta(seconds=COOLDOWN_DURATION):
                    image_uploads[server_id] = {"count": 1, "timestamp": current_time}
                else:
                    image_uploads[server_id]["count"] += 1
                    image_uploads[server_id]["timestamp"] = current_time

                # Check if the server has exceeded the image limit
                if image_uploads[server_id]["count"] > IMAGE_LIMIT:
                    await message.delete()
                    warning_message = await message.channel.send(f"Slow down, {message.author.mention}. The server has reached the attachment limit ({IMAGE_LIMIT} attachments/{COOLDOWN_DURATION} seconds). Try again later or, if someone is spamming, ping the staff team!", delete_after=5)
                    # await asyncio.sleep(4)
                    # await warning_message.delete()
                    return

    await client.process_commands(message)

@client.event
async def on_thread_create(thread: nextcord.Thread):
    # Check if the thread belongs to the target forum channel
    if thread.parent_id != BUG_REPORT_CHANNEL:
        return

    try:
        # Ensure the thread has started before interacting
        await thread.join()

        # Send a custom reply message to the thread author
        author_mention = thread.owner.mention if thread.owner else "Unknown"
        await thread.send(
            f"### Hi {author_mention}, thanks for reaching out! I appreciate you took time to report a bug in one of my games.\n"
            f"* Don't ping the dev! Keep in mind <@777460173115097098> might need up to 1 day to respond.\n"
            f"* Make sure to **provide a screenshot of the Roblox Developer Console** if you haven't already. Bring it up by pressing F9 or typing `/console` in chat (if available).\n"
            f"* Review the guidelines and **provide any additional details that could help me resolve the issue.** (Photos, Videos, What you were doing before, etc.)\n"
            f"Thank you for your patience & understanding!\n"
            f"-# This is an automated response, I am a bot."
        )

        apply_tag_to_thread(thread, TAGS["Open"])

        print(f"Replied to thread in bug-report: {thread.name}")

    except Exception as e:
        print(f'Failed to reply to thread in bug-report: "{thread.name}": {e}')

# Background task to clear image counts every 1 minute
@tasks.loop(seconds=60)
async def clear_image_counts():
    current_time = datetime.now()
    for server_id, data in list(image_uploads.items()):
        last_timestamp = data["timestamp"]
        if current_time - last_timestamp >= timedelta(seconds=60):
            del image_uploads[server_id]

@clear_image_counts.before_loop
async def before_clear_image_counts():
    await client.wait_until_ready()

# Constants
SENDING_CHANNEL = 1107624079210582016
REACT_CHANNELS = [1059899526992904212] 
STAR_EMOJI = "⭐"
TRIGGER_COUNT = 5
STRICT_MODE = True # Toggle strict mode. If it's on, anyone without attachments will be discarded.
BLACKLIST = [] # Add IDs of people you hate the most.

@client.event
async def on_raw_reaction_add(payload):
    if not payload.channel_id in REACT_CHANNELS:
        return
    if not payload.emoji.name == STAR_EMOJI:
        return
    channel = client.get_channel(payload.channel_id)
    message : nextcord.Message = await channel.fetch_message(payload.message_id)

    if message.author in BLACKLIST:
        return
    
    # check message id (check if this thing was already posted)
    value = None
    async with aiosqlite.connect("starboard.db") as db:
        cursor = await db.execute("SELECT * FROM starboard WHERE message_id = ?", (payload.message_id, ))
        value = await cursor.fetchone()
        print(f"Fetched value from database: {value}")
    if value:
        return

    reaction = None
    for react in message.reactions:
        if react.emoji == payload.emoji.name:
            reaction = react
            break
    if not reaction or reaction.count < TRIGGER_COUNT:
        return
    

    ctx : nextcord.channel = client.get_channel(SENDING_CHANNEL)
    content = message.content
    attachments = []
    jmp = message.jump_url
    if message.attachments != []:
        for attachment in message.attachments:
            f = await attachment.to_file()
            attachments.append(f)
    if message.attachments == [] and STRICT_MODE:
        return
    msg = await ctx.send(f":star: {reaction.count}/{str(TRIGGER_COUNT)}\nby: {message.author.mention}\nin: {jmp}", files=attachments)

    # Insert the thing into the database
    async with aiosqlite.connect("starboard.db") as db:
        await db.execute("INSERT INTO starboard (message_id, starboard_message_id) VALUES (?, ?)", (message.id, msg.id))
        await db.commit()
        print(f"Inserted into database: message_id={message.id}, starboard_message_id={msg.id}")

# print(os.getenv("TOKEN"))
client.run(os.getenv("TOKEN"))