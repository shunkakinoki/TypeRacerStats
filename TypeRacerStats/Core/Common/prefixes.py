import json
from TypeRacerStats.file_paths import *

def load_prefixes():
    with open(PREFIXES_FILE_PATH, 'r') as jsonfile:
        prefixes = json.load(jsonfile)
    return prefixes

def update_prefixes(prefixes):
    with open(PREFIXES_FILE_PATH, 'w') as jsonfile:
        json.dump(prefixes, jsonfile, indent = 4)

def get_prefix(bot, message):
    return load_prefixes()[str(message.guild.id)]
    