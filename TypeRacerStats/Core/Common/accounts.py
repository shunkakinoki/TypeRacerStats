import json
from TypeRacerStats.file_paths import ACCOUNTS_FILE_PATH

def load_accounts():
    with open(ACCOUNTS_FILE_PATH, 'r') as jsonfile:
        return json.load(jsonfile)

def update_accounts(accounts):
    with open(ACCOUNTS_FILE_PATH, 'w') as jsonfile:
        json.dump(accounts, jsonfile, indent = 4)

def check_account(discord_id):
    accounts = load_accounts()

    try:
        return lambda x: (accounts[str(discord_id)]['main'],) + x
    except KeyError:
        return lambda x: x

def account_information(discord_id):
    accounts = load_accounts()

    try:
        account = accounts[str(discord_id)]
        desslejusted = account['desslejusted']
        speed = account['speed']
        universe = account['universe']
    except KeyError:
        desslejusted = False
        speed = 'lag'
        universe = 'play'
    
    return {'desslejusted': desslejusted, 'speed': speed, 'universe': universe}
