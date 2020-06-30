import pickle, os, copy

database = None

default_db = {
        'guilds': {},
        'profiles': {}
        }


server_db = {
        'default_settings': {
            'required_stars': 3,
            'required_to_lose': 0,
            'self_star': False,
            'link_deletes': False,
            'link_edits': True,
            'nsfw': False
            },
        'messages': {},
        'channels': {},
        'leaderboard': {}
        }


class DataBase():
    def __init__(self, bot, path):
        self.locks = {}
        self.bot = bot
        self.path = path
        self.parse_database()

    def create_database(self):
        with open(self.path, 'wb+') as f:
            copy_of_default_db = copy.deepcopy(default_db)
            pickle.dump(copy_of_default_db, f)

    def parse_database(self):
        guilds = self.bot.guilds

        if not os.path.isfile(self.path):
            self.create_database()
        with open(self.path, 'rb') as f:
            self.db = pickle.load(f)
        # checks
        if 'bots' not in self.db:
            self.db['bots'] = {}
        if 'users' in self.db:
            del self.db['users']
        if 'profiles' not in self.db:
            self.db['profiles'] = {}
        for guild in guilds:
            self.add_guild(guild.id)
            for channel_id in self.db['guilds'][guild.id]['channels']:
                if 'nsfw' not in self.db['guilds'][guild.id]['channels'][channel_id]:
                    self.db['guilds'][guild.id]['channels'][channel_id]['nsfw'] = False

    def save_database(self):
        with open(self.path, 'wb') as f:
            try:
                string = pickle.dumps(self.db)
                f.write(string)
                print("Saved Database")
            except Exception as e:
                print(type(e), e)
                print(self.db)

    def add_guild(self, guild_id):
        if guild_id not in self.db['guilds'].keys():
            copy_of_server_db = copy.deepcopy(server_db)
            self.db['guilds'][guild_id] = copy_of_server_db

    def remove_guild(self, guild_id):
        if guild_id in self.db['guilds'].keys():
            del self.db['guilds'][guild_id]


def set_database(bot, path='database.pickle'):
    global database
    database = DataBase(bot, path)
