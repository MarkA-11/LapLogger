from classes import LapLogger

ibt_file = None
real_time_ibt = False
lap_logger = LapLogger(ibt_file=ibt_file, real_time_ibt=real_time_ibt)

try:
    while True:
        lap_logger.check_connection()
        if lap_logger.connected:
            lap_logger.loop()

except KeyboardInterrupt:
    print("Shutting down")
