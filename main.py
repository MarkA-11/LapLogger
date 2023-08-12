from Classes import LapLogger

lap_logger = LapLogger()

try:
    while True:
        lap_logger.check_status()
        if lap_logger.connected and lap_logger.active:
            lap_logger.loop()

except KeyboardInterrupt:
    print("Shutting down")
