import irsdk
import time
from datetime import datetime
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
        self.ir.freeze_var_buffer_latest()


class LapLogger(DataLogger):

    def __init__(self):
        name = "lap logger"
        version = "0.1"
        sample_rate = 1
        super().__init__(name=name, version=version, sample_rate=sample_rate)

        self.laps_complete = 0
        self.fuel_level = 0
        self.last_lap_fuel_str = ''
        self.collect_lap_time = False
        self.collect_delay_tgt = 3*self.sample_rate
        self.collect_delay_count = 0
        self.last_lap_time_str = ''
        self.data_key_ls = ['Lap', 'LapCompleted', 'LapLastLapTime', 'FuelLevel']
        self.session_lap_data = []

    def event_activated(self):
        super().event_activated()
        self.laps_complete = self.ir['LapCompleted']
        self.fuel_level = self.ir['FuelLevel']

        start_str = f"Starting fuel: {self.fuel_level}"

        print(start_str)
        self.session_lap_data = []
        self.session_lap_data.append(start_str)

    def event_deactivated(self):
        super().event_deactivated()
        self.export_data()

    def loop(self):
        super().loop()
        telem_dict = {}
        for data_key in self.data_key_ls:
            telem_dict[data_key] = self.ir[data_key]

        # if a new lap has been completed then get the fuel string and trigger delayed collection of the lap time
        if telem_dict['Lap'] > self.laps_complete:
            self.last_lap_fuel_str = str(round(self.fuel_level - telem_dict['FuelLevel'], 2) + "L")
            self.fuel_level = telem_dict['FuelLevel']
            self.collect_lap_time = True
            self.collect_delay_count = 0
            self.laps_complete = telem_dict['Lap']

        # if a lap time is to be collected and target delay has been reached then get the lap time str
        if self.collect_lap_time and self.collect_delay_count > self.collect_delay_tgt:
            self.last_lap_time_str = get_laptime_str(telem_dict['LapLastLapTime'])
            self.collect_lap_time = False
            lap_data_str = f"{self.last_lap_time_str}\t\t{self.last_lap_fuel_str}"
            print(lap_data_str)
            self.session_lap_data.append(lap_data_str)
            # reset the strings to make sure the same data cannot be dumped multiple times
            self.last_lap_time_str = ''
            self.last_lap_fuel_str = ''
        # if the target collection delay has not been reached increment the counter
        elif self.collect_lap_time:
            self.collect_delay_count += 1

    def export_data(self):
        file_name_str = datetime.now().strftime("%d-%m-%y_%H-%M-%S")+".txt"
        with open(file_name_str, 'w') as file:
            for data_line in self.session_lap_data:
                file.write(data_line+"\n")


