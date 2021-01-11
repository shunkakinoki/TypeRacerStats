import json
from TypeRacerStats.file_paths import ALIASES_FILE_PATH

command_aliases = {}
with open(ALIASES_FILE_PATH, 'r') as jsonfile:
    commands_ = json.load(jsonfile).values()

normalized_commands = {}

for category in commands_:
    for command in category:
        aliases = command['aliases']
        if aliases:
            name = command['name']
            command_aliases.update({name: aliases})
            for alias in aliases:
                normalized_commands.update({alias: name})
        normalized_commands.update({name: name})

def get_aliases(command_):
    try:
        return command_aliases[command_]
    except KeyError:
        return []
