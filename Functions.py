

def get_laptime_str(laptime: float) -> str:
    mins = int(laptime//60)
    secs = int((laptime - (mins*60))//1)
    tenths = round(laptime - ((mins*60)+secs), 2)
    tenths_str = str(tenths).split(".")[1]
    if tenths < .10:
        tenths_str = "0"+tenths_str

    if mins < 10:
        mins_str = "0"+str(mins)
    else:
        mins_str = str(mins)
    if secs < 10:
        secs_str = "0"+str(secs)
    else:
        secs_str = str(secs)
    return_str = f"{str(mins_str)}:{str(secs_str)}.{tenths_str}"

    return return_str
