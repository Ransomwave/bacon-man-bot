# Bacon Man Bot

Bacon Man is a Discord bot built using [Nextcord](https://github.com/nextcord/nextcord) that provides many nice features for managing your Discord server.

Bacon Man is designed to be self-hosted. This allows me to take many liberties with commands & goodies that would otherwise not be possible since they may not scale well for a public bot in 10,000 servers.

## Commands

- **Roblox Game Stats (`/stats`)**: Fetches and displays game statistics for supported games.
- **Media-only channels (`/mediaonly_add`, `/mediaonly_remove`, `/mediaonly_list`)**: Create and manage channels that only allow media attachments.
- **Autoreact (`/autoreact_add`, `/autoreact_remove`, `/autoreact_list`, `/autoreact_deregister`)**: Add and manage automatic reactions to messages on specific channels.
- **Reaction roles (`/reaction_roles_add`, `/reaction_roles_remove`, `/reaction_role_list`, `/reaction_role_message_create`, `/reaction_role_message_edit`, `/reaction_role_message_delete`)**: Create and manage reaction roles for server members.

## Capabilities

- **Bug Report Management (`/close`)**: Manages bug report threads, allowing you to close them with a specified reason.
- **Starboard Functionality**: Allows users to star messages, which are then displayed in a dedicated starboard channel after reaching a certain threshold.
- **Attachment Limit Enforcement**: Enforces limits on the number of attachments in messages per minute to prevent spam or disrupting conversations.
- **Customizable Settings**: Provides options for server administrators to customize the bot's behavior and responses.
