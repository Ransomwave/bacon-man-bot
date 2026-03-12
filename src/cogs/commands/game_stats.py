from bs4 import BeautifulSoup
import nextcord
from nextcord.ext.commands import Cog
import requests


class GameStatsCommand(Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="stats", description="Get live stats for a Roblox game given it's ID"
    )
    async def stats(
        self,
        interaction: nextcord.Interaction,
        id: int = nextcord.SlashOption(
            name="id", description="The ID of the Roblox game", required=False
        ),
    ):
        id = id or 8197423034
        url = f"https://www.roblox.com/games/{id}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        game_name = soup.find("h1", class_="game-name").text.strip()
        universeIdUrl = f"https://apis.roblox.com/universes/v1/places/{id}/universe"

        universeJSON = requests.get(universeIdUrl)
        universeJSON = universeJSON.json()
        universeID = universeJSON["universeId"]

        playersUrl = f"https://games.roblox.com/v1/games?universeIds={universeID}"

        response = requests.get(playersUrl)
        response = response.json()
        response = response.get("data")[0]

        playing = response["playing"]
        visits = response["visits"]
        favourites = response["favoritedCount"]
        creator = response["creator"]["name"]
        # favourites = "{:,}".format(response['favoritedCount'])
        # favourites = f"{int(response['favoritedCount']):,}"

        iconUrl = f"https://thumbnails.roblox.com/v1/games/icons?universeIds={universeID}&size=150x150&format=Png&isCircular=false"
        iconRequest = requests.get(iconUrl)
        iconJSON = iconRequest.json()
        icon = iconJSON["data"][0]["imageUrl"]

        embed = nextcord.Embed(
            title="Game Stats:", description=f"{game_name} ({id})", color=0xFF4747
        )
        embed.set_thumbnail(url=icon)
        embed.add_field(name="Creator:", value=creator, inline=False)
        embed.add_field(name="Concurrent Players:", value=playing, inline=True)
        embed.add_field(name="Visit Count:", value=visits, inline=True)
        embed.add_field(name="Favorite Count:", value=favourites, inline=False)
        embed.add_field(name="Universe ID:", value=universeID, inline=False)

        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(GameStatsCommand(bot))
