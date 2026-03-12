import importlib
import inspect

from config import *
from utils import *
from bot import Bot
import nextcord
from nextcord.ext.commands import Cog
from dotenv import load_dotenv
import os, logging


def main():

    # Create the logs folder if it doesn't exist
    if not os.path.exists("logs"):
        os.mkdir("logs")

    # Create the nextcord debug logger
    nextcord_logger = Logger(
        "nextcord", "logs/nextcord.log", level=logging.DEBUG, print_level=100
    )

    # Create the bot
    bot = Bot(intents=nextcord.Intents.all())

    # Load the environment variables
    load_dotenv()

    # Get the token from the environment variables
    token = os.getenv("TOKEN")
    if not token:
        bot.logger.critical(
            "No token found in the environment variables, please ensure that you have a .env file in the root directory of the project with a TOKEN variable"
        )
        exit(1)

    # Try to load all the cogs
    for cog in get_cogs():
        try:
            cog_module = importlib.import_module(cog)

            # if hasattr(cog_module, "setup"):
            # "Traditional" extension loading, cog must have a "setup" function
            bot.load_extension(cog)

            # else:
            #     # "Non-standard" (easier) cog loading, look for a class that inherits from Cog and load it
            #     # Considering this bot is only meant to run in one server, this is fine and allows for much less boilerplate code when creating cogs

            #     cog_classes = [
            #         obj
            #         for _, obj in inspect.getmembers(cog_module, inspect.isclass)
            #         if issubclass(obj, Cog)
            #         and obj is not Cog
            #         and obj.__module__ == cog_module.__name__
            #     ]

            #     if len(cog_classes) == 1:
            #         bot.add_cog(cog_classes[0](bot))
            #     elif len(cog_classes) == 0:
            #         raise TypeError(f"{cog} has no setup function or Cog subclass")
            #     else:
            #         raise TypeError(
            #             f"{cog} has multiple Cog subclasses and no setup function"
            #         )

            bot.logger.debug("Loaded " + cog)

        except Exception as e:
            bot.logger.error(e)
            bot.logger.exception(e)

    # Try to run the bot
    try:
        bot.run(token)
    except nextcord.LoginFailure as e:
        bot.logger.critical(
            "Failed to login, please ensure that the token in the .env file is valid"
        )
        bot.logger.exception(e)
        exit(1)


if __name__ == "__main__":
    main()
