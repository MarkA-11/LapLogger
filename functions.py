def get_time_str(laptime_float) -> str:
    if not laptime_float or (laptime_float and laptime_float < 0):
        return_str = 'No data'
    else:
        mins, secs = divmod(laptime_float, 60)
        tenths = (laptime_float - (int(mins) * 60 + int(secs))) * 100
        time_ls = [int(mins // 1), int(secs // 1), int(tenths // 1)]
        return_str = "{:02d}:{:02d}.{:02d}".format(*time_ls)
    return return_str


def ms_to_mph_str(ms_speed_float) -> str:
    mph_val = round((ms_speed_float * 3600) / 1609, 2)
    mph_str = mph_val = str(mph_val) + " MPH"
    return mph_str


def ms_to_kph_str(ms_speed_float) -> str:
    kph_val = round((ms_speed_float * 3600) / 1000, 2)
    kph_str = str(kph_val) + " KPH"
    return kph_str