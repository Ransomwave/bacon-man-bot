MAX_LENGTH = 2000


def truncate_to_discord_max_length(input_str: str) -> str:
    if len(input_str) > MAX_LENGTH:
        return input_str[:MAX_LENGTH]
    return input_str
