import irsdk
import time
from datetime import datetime
from Functions import get_laptime_str


class DataLogger:

    def __init__(self, name, version, data_key_ls, sample_rate):
        self.ir = irsdk.IRSDK()
        self.connected = False
        self.active = False
        self.name = name
        self.version = version
        self.sample_rate = sample_rate  # samples per second, maximum 60
        self.data_key_ls = data_key_ls
        self.tick_dict = dict.fromkeys(data_key_ls)

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

    # replace this with an event handler function with different sub functions ?
    def event_connected(self):
        print(f"\n{self.name} connected")

    def event_disconnected(self):
        self.ir.shutdown()
        print(f"\n{self.name} disconnected")

    def event_activated(self):
        print(f"\n{self.name} activated")

    def event_deactivated(self):
        print(f"\n{self.name} deactivated")

    def loop(self):
        time.sleep(1/self.sample_rate)
        self.ir.freeze_var_buffer_latest()
        for data_key in self.tick_dict.keys():
            self.tick_dict[data_key] = self.ir[data_key]
        self.ir.unfreeze_var_buffer_latest()


class LapLogger(DataLogger):

    def __init__(self):
        name = "lap logger"
        version = "0.1"
        sample_rate = 2
        data_key_ls = ['Lap', 'LapCompleted', 'LapLastLapTime']
        super().__init__(name=name, version=version, data_key_ls=data_key_ls, sample_rate=sample_rate)

        self.laps_complete = 0
        self.session_lap = 0
        self.lap_log_dict = {'lap': [],
                             'time': []}

        # replace this with a counter / collector class ?
        collect_delay_tgt_secs = 2  # delay before collecting the last lap time - about 60 ticks so 2 secs should be ok
        self.collect_delay_tgt = collect_delay_tgt_secs*self.sample_rate
        self.collect_lap_time = False
        self.collect_delay_count = 0

    def event_activated(self):
        super().event_activated()
        self.laps_complete = self.ir['Lap']
        self.session_lap = 0
        self.lap_log_dict = {'lap': [],
                             'time': []}
        self.add_start_data()

    def event_deactivated(self):
        print("\n")
        self.generate_summary()
        print("\nStopping lap logging session")
        super().event_deactivated()

    def loop(self):
        super().loop()

        # if a new lap has been completed then trigger delayed collection of the lap time
        # (last lap time updates a little while after the car crosses the line)
        if self.tick_dict['Lap'] > self.laps_complete:
            self.laps_complete = self.tick_dict['Lap']
            # set the lap time collect flag and reset the counter
            self.collect_lap_time = True
            self.collect_delay_count = 0
            # need to get any other data at this point too i.e. fuel used

        # if waiting to collect a lap time and target delay has been reached then get the lap time str
        if self.collect_lap_time and self.collect_delay_count >= self.collect_delay_tgt:
            # reset the collect flag and the counter
            self.collect_lap_time = False
            self.collect_delay_count = 0
            # get the last lap time as a string and print it
            last_lap_time_str = get_laptime_str(self.tick_dict['LapLastLapTime'])
            print(f"Lap {str(self.session_lap)}:\t{last_lap_time_str}")
            # add lap and time to the data log dict
            self.lap_log_dict['lap'].append(self.session_lap)
            self.lap_log_dict['time'].append(self.tick_dict['LapLatLapTime'])
            # increment logging session lap number (after printing lap_time_str so that lap 0 is the out lap)
            self.session_lap += 1
        # if waiting to collect a lap time and target delay not reached increment the counter
        elif self.collect_lap_time:
            self.collect_delay_count += 1

    def add_start_data(self):
        track_str = ''
        if self.ir['WeekendInfo']['TrackDisplayName']:
            track_str = track_str + self.ir['WeekendInfo']['TrackDisplayName']
            if self.ir['WeekendInfo']['TrackConfigName']:
                track_str = track_str + " - " + self.ir['WeekendInfo']['TrackConfigName']
        if self.ir['WeekendInfo']['TrackSurfaceTemp']:
            track_str = track_str + f", Track temp: {self.ir['WeekendInfo']['TrackSurfaceTemp']}"

        driver_idx = self.ir['DriverInfo']['DriverCarIdx']
        car_str = ''
        car_str = car_str + self.ir['DriverInfo']['Drivers'][driver_idx]['CarScreenName']
        car_str = car_str + f", set up: {self.ir['DriverInfo']['DriverSetupName']}"
        car_str = car_str + f", Starting fuel: {str(round(self.ir['FuelLevel'], 2))} Litres"

        print("\nStarting lap logging session..\n")
        print(track_str)
        print(car_str)
        print("\nSession lap times:")

    def generate_summary(self):
        # generate a lap time summary (excluding the out lap)
        fastest_time = min(self.lap_log_dict['time'][1:])
        slowest_time = max(self.lap_log_dict['time'][1:])
        total_time = sum(self.lap_log_dict['time'][1:])
        mean_time = total_time / (len(self.lap_log_dict['time']) - 1)

        fastest_delta = abs(fastest_time - mean_time)
        slowest_delta = abs(slowest_time - mean_time)

        fastest_str = get_laptime_str(fastest_time)
        mean_str = get_laptime_str(mean_time)
        slowest_str = get_laptime_str(slowest_time)
        fastest_delta_str = str(round(fastest_delta, 2))
        slowest_delta_str = str(round(slowest_delta, 2))

        print(f"\nLap time summary - \n\tMean: {mean_str}, "
              f"Fastest: {fastest_str} (-{fastest_delta_str}s to mean), "
              f"Slowest: {slowest_str} (+{slowest_delta_str}s to mean)\n")
