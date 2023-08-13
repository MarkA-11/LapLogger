

def get_laptime_str(laptime_float) -> str:
    if not laptime_float or (laptime_float and laptime_float < 0):
        return_str = 'No data'
    else:
        mins, secs = divmod(laptime_float, 60)
        tenths = (laptime_float - (int(mins) * 60 + int(secs))) * 100
        time_ls = [int(mins // 1), int(secs // 1), int(tenths // 1)]
        return_str = "{:02d}:{:02d}.{:02d}".format(*time_ls)
    return return_str
