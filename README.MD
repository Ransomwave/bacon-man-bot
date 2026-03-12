# Bacon Man Bot

Bacon Man Bot is a Discord bot built using Nextcord (a fork of Discord.py) that provides various functionalities including game stats retrieval, starboard functionality, attachment limit enforcement, and more.

This bot was built for managing my own Discord, with features being made to bring solutions to my problems that no other bot offered.

## Capabilities

- **Game Stats**: Retrieve stats for Roblox games using the `/stats` command.
- **Starboard**: Automatically post messages that receive a certain number of star reactions to a designated starboard channel.
  - **Blacklist**: Maintain a blacklist of users whose messages will not be considered for the starboard.
  - **Strict Mode**: Optionally require messages to have attachments to be eligible for the starboard.
- **Attachment Limit**: Enforce a limit on the number of attachments in messages.
  - **Configurable Limit**: Set a custom attachment limit for messages.
  - **Attachment Deletion**: Automatically delete attachments that exceed the specified limit.
- **Bug Report Management**: Close bug report threads with a specified reason.
- **Customizable Settings**: Configure various settings such as starboard channels, trigger counts, and more.
