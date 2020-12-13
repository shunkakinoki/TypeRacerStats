import json
from TypeRacerStats.config import DEFAULT_COMMAND_PREFIX
from TypeRacerStats.file_paths import PREFIXES_FILE_PATH

def load_prefixes():
    with open(PREFIXES_FILE_PATH, 'r') as jsonfile:
        prefixes = json.load(jsonfile)
    return prefixes

def update_prefixes(prefixes):
    with open(PREFIXES_FILE_PATH, 'w') as jsonfile:
        json.dump(prefixes, jsonfile, indent = 4)

def get_prefix(bot, message):
    try:
        return load_prefixes()[str(message.guild.id)]
    except KeyError:
        return DEFAULT_COMMAND_PREFIX
    except AttributeError:
        return DEFAULT_COMMAND_PREFIX
