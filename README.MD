# Bacon Man Bot

Bacon Man Bot is a Discord bot built using Nextcord (a fork of Discord.py) that provides various functionalities including game stats retrieval, starboard functionality, attachment limit enforcement, and more.

This bot was built for managing my own Discord, with features being made to bring solutions to my problems that no other bot offered.

## Capabilities

- **Ping Command**: Get the bot's latency.
- **Game Stats Command**: Retrieve stats for a specified Roblox game.
- **Starboard Functionality**: Automatically add messages with a certain number of star reactions to a starboard channel.
- **Attachment Limit Enforcement**: Limit the number of attachments a server can upload within a certain time frame.
- **Bug Report Thread Handling**: Automatically reply to new threads in the bug report forum channel & manage tags (open, fixed, closed...).

## Commands

- **/help**: Show available commands and their usage.
- **/ping**: Get the bot's latency.
- **/whoishosting**: Get the hostname of the machine running the bot (DEV ONLY).
- **/stats [id]**: Get a game's stats. If no ID is provided, it defaults to the game "Get a Drink at 3 AM".
- **/close \<reason\> [lock?]**: Closes a bug report thread on my server.
