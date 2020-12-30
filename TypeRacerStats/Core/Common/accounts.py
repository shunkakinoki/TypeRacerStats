import json
import sqlite3
import sys
sys.path.insert(0, '')
from TypeRacerStats.config import USERS_KEY
from TypeRacerStats.file_paths import ACCOUNTS_FILE_PATH, DATABASE_PATH

def load_accounts():
    with open(ACCOUNTS_FILE_PATH, 'r') as jsonfile:
        return json.load(jsonfile)

def update_accounts(accounts):
    with open(ACCOUNTS_FILE_PATH, 'w') as jsonfile:
        json.dump(accounts, jsonfile, indent = 4)

def check_account(discord_id):
    accounts = load_accounts()

    try:
        account = accounts[str(discord_id)]['main']
        return lambda x: (account,) + x
    except KeyError:
        return lambda x: x

def account_information(discord_id):
    accounts = load_accounts()

    try:
        account = accounts[str(discord_id)]
        desslejusted = account['desslejusted']
        universe = account['universe']
    except KeyError:
        desslejusted = False
        universe = 'play'

    return {'desslejusted': desslejusted, 'universe': universe}

def check_banned_status(ctx):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    try:
        user_data = c.execute(f"SELECT * FROM {USERS_KEY} WHERE id = ?", (ctx.message.author.id,)).fetchall()
    except sqlite3.OperationalError:
        c.execute(f"CREATE TABLE {USERS_KEY} (id integer PRIMARY KEY, banned BOOLEAN)")

    conn.close()

    return True if not user_data else not user_data[0][1]
