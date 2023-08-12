import irsdk
import time
from Functions import get_laptime_str


class DataLogger:

    def __init__(self, name, version, sample_rate):
        self.ir = irsdk.IRSDK()
        self.connected = False
        self.active = False
        self.name = name
        self.version = version
        self.sample_rate = sample_rate  # samples per second, maximum 60

        print(f"{self.name} version {self.version} starting")

    def check_status(self):
        if not self.connected and self.ir.startup():
            self.connected = True
            self.event_connected()

        elif self.connected and not self.ir.is_connected:
            self.connected = False
            self.event_disconnected()

        elif self.connected:
            if not self.active and self.ir['IsOnTrack']:
                self.active = True
                self.event_activated()

            elif self.active and not self.ir['IsOnTrack']:
                self.active = False
                self.event_deactivated()

    def event_connected(self):
        print(f"{self.name} connected")

    def event_disconnected(self):
        self.ir.shutdown()
        print(f"{self.name} disconnected")

    def event_activated(self):
        print(f"{self.name} activated")

    def event_deactivated(self):
        print(f"{self.name} deactivated")

    def loop(self):
        time.sleep(1/self.sample_rate)


class LapLogger(DataLogger):

    def __init__(self):
        name = "lap logger"
        version = "0.1"
        sample_rate = 15
        super().__init__(name=name, version=version, sample_rate=sample_rate)
        
    def loop(self):
        super().loop()
