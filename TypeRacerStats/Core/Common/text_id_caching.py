tids = dict()

def cache_id(channel_id, tid):
    tids.update({channel_id: tid})

def get_cached_id(channel_id):
    return tids.get(channel_id, False)
