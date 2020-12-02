import re

def seconds_to_text(seconds, *args):
    if len(args) > 1: return
    elif len(args) == 1: addS = args[0]
    else: addS = False

    if seconds == 0: return 0
    days = int(seconds // 86400)
    seconds %= 86400
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds = round(seconds % 60, 3)

    days_text = ''
    if days: days_text = f"{f'{days:,}'} days"
    if days == 1 or (days and addS): days_text = f"{f'{days:,}'} day"
    days_comma = ''
    if days and (hours or minutes or seconds): days_comma = ', '

    hours_text = ''
    if hours: hours_text = f"{hours} hours"
    if hours == 1 or (hours and addS): hours_text = f"{hours} hour"
    hours_comma = ''
    if hours and (minutes or seconds): hours_comma = ', '

    minutes_text = ''
    if minutes: minutes_text = f"{minutes} minutes"
    if minutes == 1 or (minutes and addS): minutes_text = f"{minutes} minute"
    minutes_comma = ''
    if minutes and seconds: minutes_comma = ', '

    seconds_text = ''
    if seconds: seconds_text = f"{seconds} seconds"
    if seconds == 1 or (seconds and addS): seconds_text = f"{seconds} second"
    return days_text + days_comma + hours_text + hours_comma + minutes_text + minutes_comma + seconds_text

def num_to_text(n):
    endings = ['th', 'st', 'nd', 'rd']
    try:
        ending = endings[n % 10]
    except IndexError:
        ending = 'th'
    if n % 100 - n % 10 == 10: ending = 'th'
    return f"{f'{n:,}'}{ending}"

def href_universe(universe):
    return f"[`{universe}`](https://play.typeracer.com/?universe={universe})"

escape_sequence = lambda x: bool(re.findall('[^a-z^0-9^_]', x.lower()))