import json
from TypeRacerStats.file_paths import TEXTS_FILE_PATH

def load_difficulties():
    with open(f"{TEXTS_FILE_PATH}/text_difficulties.json", 'r') as jsonfile:
        ret = json.load(jsonfile)
    return ret

def load_player_top_tens():
    with open(f"{TEXTS_FILE_PATH}/player_top_tens.json", 'r') as jsonfile:
        ret = json.load(jsonfile)
    return ret

def load_texts_large():
    with open(f"{TEXTS_FILE_PATH}/texts_large.json", 'r') as jsonfile:
        ret = json.load(jsonfile)
    return ret

def load_texts_json():
    with open(f"{TEXTS_FILE_PATH}/texts.json", 'r') as jsonfile:
        ret = json.load(jsonfile)
    return ret
