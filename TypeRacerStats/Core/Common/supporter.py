from TypeRacerStats.Core.Common.accounts import check_account
from TypeRacerStats.file_paths import SUPPORTERS_FILE_PATH
from TypeRacerStats.config import MAIN_COLOR
import json
import sys
sys.path.insert(0, '')


def load_supporters():
    with open(SUPPORTERS_FILE_PATH, 'r') as jsonfile:
        supporters = json.load(jsonfile)
    return supporters


def update_supporters(supporters):
    with open(SUPPORTERS_FILE_PATH, 'w') as jsonfile:
        json.dump(supporters, jsonfile, indent=4)


def get_supporter(id_):
    try:
        supporter = load_supporters()[str(id_)]
        if int(supporter['tier']) >= 2:
            return supporter['color']
        else:
            return MAIN_COLOR
    except KeyError:
        return MAIN_COLOR


def get_graph_colors(id_):
    graph_colors = dict()
    try:
        supporter = load_supporters()[str(id_)]
        if int(supporter['tier']) >= 3:
            graph_colors = supporter['graph_color']
        else:
            raise KeyError
    except KeyError:
        graph_colors = {
            'bg': None,
            'graph_bg': None,
            'axis': None,
            'line': None,
            'text': None,
            'grid': None,
            'cmap': None
        }

    account = check_account(id_)(())
    if account:
        graph_colors.update({'user': account[0]})
    else:
        graph_colors.update({'user': '!'})

    return graph_colors


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
