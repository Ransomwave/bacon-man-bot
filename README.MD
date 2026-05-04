# Bacon Man Bot

Bacon Man is a Discord bot built using [Nextcord](https://github.com/nextcord/nextcord) that provides many nice features for managing your Discord server.

This bot was originally built for managing my own Discord, adding features that no other bot offered or that required multiple bots.

## Commands

- **Game Stats Retrieval (`/stats`)**: Fetches and displays game statistics for supported games.
- **Media-only channels (`/mediaonly_add`, `/mediaonly_remove`, `/mediaonly_list`)**: Create and manage channels that only allow media attachments.
- **Autoreact (`/autoreact_add`, `/autoreact_remove`, `/autoreact_list`, `/autoreact_deregister`)**: Add and manage automatic reactions to messages on specific channels.
- **Reaction roles (`/reaction_roles_add`, `/reaction_roles_remove`, `/reaction_role_list`, `/reaction_role_message_create`, `/reaction_role_message_edit`, `/reaction_role_message_delete`)**: Create and manage reaction roles for server members.

## Capabilities

- **Bug Report Management (`/close`)**: Manages bug report threads, allowing you to close them with a specified reason.
- **Starboard Functionality**: Allows users to star messages, which are then displayed in a dedicated starboard channel.
- **Attachment Limit Enforcement**: Enforces limits on the number of attachments in messages to prevent spam.
- **Customizable Settings**: Provides options for server administrators to customize the bot's behavior and responses.
