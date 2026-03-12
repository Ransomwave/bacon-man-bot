import nextcord

from utils import logger

log = logger.Logger("ThreadUtils", "logs/bot.log")


async def apply_tag(thread: nextcord.Thread, tag_id: int):
    # Fetch the forum channel that owns this thread
    forum_channel = thread.parent

    # Find the tag by its ID
    tagToApply = nextcord.utils.get(forum_channel.available_tags, id=tag_id)

    if tagToApply is None:
        log.error(
            f"Attempted to apply Tag with ID {tag_id} to Thread {thread.name}, but it was not found by nextcord."
        )
    else:
        applied_tags = thread.applied_tags
        applied_tags.insert(
            0, tagToApply
        )  # Insert the tag object at the beginning of the list
        log.debug(f"Applied tag: {tagToApply.name} to thread: {thread.name}")

        # Apply the updated tags to the thread
        await thread.edit(applied_tags=applied_tags)


async def remove_tag(thread: nextcord.Thread, tag_id: int):
    # Fetch the forum channel that owns this thread
    forum_channel = thread.parent

    # Find the tag by its ID
    tagToRemove = nextcord.utils.get(forum_channel.available_tags, id=tag_id)

    if tagToRemove is None:
        log.error(
            f"Attempted to remove Tag with ID {tag_id} from Thread {thread.name}, but it was not found by nextcord."
        )
    else:
        applied_tags = (
            thread.applied_tags.copy()
        )  # Create a copy to avoid modifying the original

        # Remove the tag if it exists in the applied tags
        if tagToRemove in applied_tags:
            applied_tags.remove(tagToRemove)
            log.debug(f"Removed tag: {tagToRemove.name} from thread: {thread.name}")
            log.debug(
                f"Updated applied tags: {[tag.name for tag in applied_tags].join(', ')}"
            )

            # Apply the updated tags to the thread
            await thread.edit(applied_tags=applied_tags)
        else:
            log.debug(
                f"Tag {tagToRemove.name} was not applied to the thread, nothing to remove."
            )
