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

def get_supporter(id_):
    try:
        supporter = load_supporters()[str(id_)]
        if int(supporter['tier']) >= 2:
            return supporter['color']
        else:
            return MAIN_COLOR
    except KeyError:
        return MAIN_COLOR

def check_dm_perms(ctx, tier):
    if ctx.message.guild:
        return True
    try:
        id_ = ctx.message.author.id
        supporter = load_supporters()[str(id_)]
        if int(supporter['tier']) >= tier:
            return True
        else:
            return False
    except KeyError:
        return False
