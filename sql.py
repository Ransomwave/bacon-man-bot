from data import StarboardDatabase
import aiosqlite

# init_db(), write_data(id : int), has_id(id: int)

class SQLStarboard(StarboardDatabase):
    def __init__(self):
        self.filename = "starboard.db" # Filename for your little database.

    async def init_db(self):
        print("Chosen database: SQL\nInitializing the database...")
        async with aiosqlite.connect(self.filename) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS starboard (message_id INTEGER PRIMARY KEY)")
            await db.commit()
            print("DB ready")

    async def write_data(self, id : int):
        async with aiosqlite.connect(self.filename) as db:
            await db.execute("INSERT INTO starboard (message_id) VALUES ( ? )", (id, ))
            await db.commit()

    async def has_id(self, id : int) -> bool:
        async with aiosqlite.connect(self.filename) as db:
            cur = await db.execute("SELECT * FROM starboard WHERE message_id = ?", (id, ))
            value = await cur.fetchone()
            if value:
                return True
            return False