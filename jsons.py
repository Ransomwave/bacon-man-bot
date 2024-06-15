from json import load, dump
from data import StarboardDatabase

# init_db(), write_data(id : int), has_id(id: int)

class JSONStarboard(StarboardDatabase):
    def __init__(self):
        self.filename = "starboard.json" # 🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎🐎
        self.data = {} # The JSON data. It does save and sync with the file obv

    async def init_db(self):
        print("Chosen database: JSON\nInitializing the database...")
        json = None
        try:
            json = open(self.filename, "r")
        except FileNotFoundError:
            json = open(self.filename, "x")
            return
        self.data = load(json)
        
    async def write_data(self, id : int):
        self.data[id] = id
        json = open(self.filename, "w")
        dump(self.data, json)

    async def has_id(self, id : int):
        if id in self.data:
            return True
        else:
            return False