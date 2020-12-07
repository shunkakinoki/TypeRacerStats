import json
from TypeRacerStats.config import MAIN_COLOR
from TypeRacerStats.file_paths import SUPPORTERS_FILE_PATH

def load_supporters():
    with open(SUPPORTERS_FILE_PATH, 'r') as jsonfile:
        supporters = json.load(jsonfile)
    return supporters

def update_supporters(supporters):
    with open(SUPPORTERS_FILE_PATH, 'w') as jsonfile:
        json.dump(supporters, jsonfile, indent = 4)

def get_supporter(id):
    try:
        return load_supporters()[str(id)]
    except KeyError:
        return MAIN_COLOR
