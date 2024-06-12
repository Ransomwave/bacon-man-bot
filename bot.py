import nextcord as discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta  # Import the datetime module
import asyncio, aiosqlite
import re


#discord
client = commands.Bot(command_prefix = '!', intents = discord.Intents.all())

##
url = "https://www.roblox.com/games/8197423034/get-a-drink-at-3-am-beta"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
##

# Initializes the starboard SQLite table (obviously)
async def _create_starboard_table(): 
    async with aiosqlite.connect("starboard.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS starboard (
        message_id INTEGER PRIMARY KEY,
        starboard_message_id INTEGER,
        star_count INTEGER)
        ''')
        await db.commit()

@client.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.playing, name="get a drink at 3 am!")
    await client.change_presence(status=discord.Status.online, activity=activity)
    await _create_starboard_table()
    print('=============== RUNNING ===============')

@client.slash_command(name="ping", description="Get the bot's latency.")
async def ping(ctx):
    latency = client.latency * 1000
    embed = discord.Embed(colour=discord.Colour.red())
    embed.add_field(name="Client Latency", value=f"Ping value: **{latency}ms**")
    await ctx.send(embed=embed)

# @client.slash_command(name="currentplr", description="Get gada3's current playercount")
# async def currentplr(ctx):
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, 'html.parser')

#     active_players = soup.select_one('li.game-stat.game-stat-width p.text-lead.font-caption-body')

#     await ctx.send(f"current player count: {active_players.text}")

@client.slash_command(name="stats", description="Get a game's stats", guild_ids=[995400838136746154])
async def stats(ctx, id: int = 8197423034):
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

    embed = discord.Embed(title="Game Stats:", description=f"{game_name} ({id})", color=0xff4747)
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Creator:", value=creator, inline=False)
    embed.add_field(name="Current Player Count:", value=playing, inline=True)
    embed.add_field(name="Visit Count:", value=visits, inline=True)
    embed.add_field(name="Favorite Count:", value=favourites, inline=False)
    embed.add_field(name="Universe ID:", value=universeID, inline=False)
    await ctx.send(embed=embed)

@client.slash_command(description="Show available commands and their usage")
async def help(ctx):
    embed = discord.Embed(title="Command List", color=0xff4747)
    
    # Ping Command
    ping_description = "Get the bot's latency."
    ping_usage = "/ping"
    embed.add_field(name="/ping", value=f"Description: {ping_description}\nUsage: `{ping_usage}`", inline=False)
    
    # Stats Command
    stats_description = "Get a game's stats."
    stats_usage = "/stats [id (leave blank for gada3 stats)]"
    embed.add_field(name="/stats", value=f"Description: {stats_description}\nUsage: `{stats_usage}`", inline=False)

    embed.add_field(name="Client Events", value="This bot has a few Client Events\n- Add vote reactions to all messages in a channel.\n- Limit media every 60 seconds to prevent attachment spam.\nMore Roblox-related functionality will be added in the future!", inline=False)

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
async def on_message(message):
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

        if message.attachments or re.search(r'(https?://(?:www\.)?tenor\.com/.+|https?://\S+\.gif)', message.content):

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
                    warning_message = await message.channel.send(f"Slow down, {message.author.mention}. The server has reached the attachment limit ({IMAGE_LIMIT} images/{COOLDOWN_DURATION} seconds). Try again later or, if someone's spamming, ping the staff team!.")
                    await asyncio.sleep(4)
                    await warning_message.delete()
                    return

    await client.process_commands(message)

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

# Constants, edit them for your own server(TM)
SENDING_CHANNEL = 0
REACT_CHANNEL = 0
STAR_EMOJI = "⭐"
TRIGGER_COUNT = 1


# please use cogs, your code is messy


@client.event
async def on_raw_reaction_add(payload):
    if not payload.channel_id == REACT_CHANNEL:
        return
    

file = open("token.txt", "r")
token = file.read()
client.run(token)
file.close()