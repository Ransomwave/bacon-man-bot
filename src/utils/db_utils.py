import logging
from typing import Dict

import aiosqlite

import config
from utils.logger import Logger

logger = Logger("db_utils", "logs/db_utils.log", print_level=logging.DEBUG)


async def create_table(table_name: str, columns: Dict[str, str]):
    """
    Creates a SQL table with the specified name and columns.

    :param table_name: The name of the table to create.
    :param columns: A dictionary where the keys are column names and the values are their data types.
    """
    column_definitions = ", ".join(
        f"{name} {data_type}" for name, data_type in columns.items()
    )
    query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions})"
    async with aiosqlite.connect(config.BOT_DATA_FILE) as db:
        await db.execute(query)
        await db.commit()
    return query


async def array_to_string(array, separator=","):
    return separator.join(array)


async def string_to_array(string, separator=","):
    return string.split(separator)


async def append_to_array_string_if_not_exists(
    array_string, new_element, separator=","
):
    array = await string_to_array(array_string, separator)
    if new_element not in array:
        array.append(new_element)
    else:
        logger.error(f"Element '{new_element}' already exists in the array.")
    return await array_to_string(array, separator)


async def remove_from_array_string(array_string, element_to_remove, separator=","):
    array = await string_to_array(array_string, separator)
    if element_to_remove in array:
        array.remove(element_to_remove)
    else:
        logger.error(f"Element '{element_to_remove}' not found in the array.")
    return await array_to_string(array, separator)
