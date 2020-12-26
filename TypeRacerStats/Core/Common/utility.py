def reduce_list(lst):
    length = len(lst)

    if length > 2000:
        return lst[::length // 1000]
    else:
        return lst
