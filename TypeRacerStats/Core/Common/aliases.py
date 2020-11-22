import json
from TypeRacerStats.file_paths import *

command_aliases = {}
with open(ALIASES_FILE_PATH, 'r') as jsonfile:
    commands_ = json.load(jsonfile).values()

for category in commands_:
    for command in category:
        if command['aliases']:
            command_aliases.update({command['name']: command['aliases']})

def get_aliases(command_):
    try:
        return command_aliases[command_]
    except KeyError:
        return []
