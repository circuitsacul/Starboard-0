import pickle

PATH = 'database.pickle'

with open(PATH, 'rb') as f:
    db = pickle.load(f)

def get_emoji(emoji):
    if type(emoji) is int:
        return emoji
    split = emoji.split(':')
    if len(split) > 2:
        try:
            emoji_id = int(split[2].replace('>', ''))
            print(1)
            return emoji_id
        except Exception as e:
            print(e)
    return emoji


#print(db)

for guild in db['guilds']:
    for channel in db['guilds'][guild]['channels']:
        new_list = []
        for emoji_str in db['guilds'][guild]['channels'][channel]['emojis']:
            new_emoji = get_emoji(emoji_str)
            new_list.append(new_emoji)
        db['guilds'][guild]['channels'][channel]['emojis'] = new_list
    for media_channel in db['guilds'][guild]['media_channels']:
        new_list = []
        for emoji_string in db['guilds'][guild]['media_channels'][media_channel]['emojis']:
            new_emoji = get_emoji(emoji_str)
            new_list.append(new_emoji)
        db['guilds'][guild]['media_channels'][media_channel]['emojis'] = new_list
    for channel, message in db['guilds'][guild]['messages']:
        new_dict = {}
        for emoji_str, data in db['guilds'][guild]['messages'][(channel, message)]['emojis'].items():
            new_emoji = get_emoji(emoji_str)
            new_dict[new_emoji] = data
        db['guilds'][guild]['messages'][(channel, message)]['emojis'] = new_dict

#print(db)
with open(PATH, 'wb') as f:
    pickle.dump(db, f)