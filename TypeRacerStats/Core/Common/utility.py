def reduce_list(lst):
    length = len(lst)

    if length > 2000:
        return lst[::length // 1000]
    else:
        return lst

def predicate(message, l, r, user_id):
    def check(reaction, user):
        if reaction.message.id != message.id or user.id != user_id:
            return False
        if l and reaction.emoji == '◀️':
            return True
        if r and reaction.emoji == '▶️':
            return True
        return False
    return check
