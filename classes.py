import irsdk
import time
from functions import get_time_str


class DataLogger:

    def __init__(self, name, version, data_key_ls, sample_rate, ibt_file=None, real_time_ibt=False):

        self.name = name
        self.version = version
        self.data_key_ls = data_key_ls
        self.sample_rate = sample_rate  # samples per second, maximum 60

        self.ir = irsdk.IRSDK()
        self.ibt = irsdk.IBT()

        self.connected = False
        self.real_time_ibt = real_time_ibt

        self.tick_dict = dict.fromkeys(data_key_ls)
        self.ibt_dict = dict.fromkeys(data_key_ls)
        self.ibt_tick = 0
        self.ibt_data = False
        self.ibt_file = ibt_file

        if self.ibt_file:
            self.ibt.open(ibt_file=ibt_file)
            self.ibt_data = True
            for data_key in self.ibt_dict.keys():
                self.ibt_dict[data_key] = self.ibt.get_all(data_key)

        print(f"{self.name} version {self.version} starting.... ")

    def check_connection(self):
        if self.ibt_file:
            if not self.connected and self.ibt_data:
                self.connected = True
                print(f"\n{self.name} processing {self.ibt_file}, connected.... ")
            elif self.connected and not self.ibt_data:
                self.connected = False
                print(f"\n{self.name} completed processing of {self.ibt_file}, disconnected.... ")
        else:
            if not self.connected and self.ir.startup():
                self.connected = True
                print(f"\n{self.name} connected to sim.... ")
            elif self.connected and not self.ir.is_connected:
                self.connected = False
                print(f"\n{self.name} disconnected from sim.... ")

    def loop(self):
        self.update_tick_dict()

    def update_tick_dict(self):
        self.wait(1 / self.sample_rate)
        if self.ibt_file:
            if self.ibt_tick < len(self.ibt_dict[self.data_key_ls[0]]):
                for data_key in self.tick_dict.keys():
                    self.tick_dict[data_key] = self.ibt_dict[data_key][self.ibt_tick]
            else:
                self.ibt_data = False
        else:
            self.ir.freeze_var_buffer_latest()
            for data_key in self.tick_dict.keys():
                self.tick_dict[data_key] = self.ir[data_key]
            self.ir.unfreeze_var_buffer_latest()

    def wait(self, secs):
        if self.ibt_file:
            self.ibt_tick += int(60 / self.sample_rate)
        if not self.ibt_file or (self.ibt_file and self.real_time_ibt):
            time.sleep(secs)


class LapLogger(DataLogger):

    def __init__(self, ibt_file=None, real_time_ibt=False):
        name = "lap logger"
        version = "0.1"
        sample_rate = 1
        data_key_ls = ['IsOnTrack', 'Lap', 'LapCompleted', 'LapLastLapTime', 'FuelLevel']

        super().__init__(name=name, version=version, data_key_ls=data_key_ls, sample_rate=sample_rate,
                         ibt_file=ibt_file, real_time_ibt=real_time_ibt)

        self.lap_log_dict = {'data': [],
                             'lap': [],
                             'time': [],
                             'fuel': []}
        self.max_collect_wait = 8  # max time in secs to wait after lap complete before collecting the last lap time

    def loop(self):
        super().loop()

        if self.tick_dict['IsOnTrack']:
            self.wait(2)
            session_lap = 0
            laps_complete = self.tick_dict['Lap']
            last_lap_time = self.tick_dict['LapLastLapTime']
            collect_lap_time = False
            lap_collect_tick = 0
            fuel_level = self.tick_dict['FuelLevel']
            start_fuel_str = str(round(fuel_level, 2)) + "L"

            print(f"\nStarting fuel {start_fuel_str}, Logging lap data.... \n")

            while self.tick_dict['IsOnTrack']:
                self.update_tick_dict()
                # check if a lap has been completed
                if self.tick_dict['Lap'] > laps_complete:
                    laps_complete = self.tick_dict['Lap']
                    self.lap_log_dict['lap'].append(session_lap)
                    session_lap += 1
                    # set the lap time collect flag to True
                    collect_lap_time = True
                    # append None as a placeholder
                    self.lap_log_dict['data'].append(None)
                    self.lap_log_dict['time'].append(None)
                    # get the fuel used, append the value and reset the fuel level
                    fuel_used = round(fuel_level - self.tick_dict['FuelLevel'], 2)
                    self.lap_log_dict['fuel'].append(fuel_used)
                    fuel_level = self.tick_dict['FuelLevel']

                if collect_lap_time and (self.tick_dict['LapLastLapTime'] != last_lap_time or
                                         lap_collect_tick >= self.max_collect_wait * self.sample_rate):
                    last_lap_time = self.tick_dict['LapLastLapTime']
                    collect_lap_time = False
                    lap_collect_tick = 0

                    self.lap_log_dict['time'][-1] = last_lap_time
                    if get_time_str(last_lap_time) != 'No data':
                        self.lap_log_dict['data'][-1] = True
                    else:
                        self.lap_log_dict['data'][-1] = False

                    lap_str = f"\tlap: {self.lap_log_dict['lap'][-1]} - " \
                              f"Time: {get_time_str(self.lap_log_dict['time'][-1])}, " \
                              f"Fuel: {self.lap_log_dict['fuel'][-1]}L"

                    if self.lap_log_dict['lap'][-1] == 0:
                        lap_str += " (out lap)"

                    print(lap_str)
                elif collect_lap_time:
                    lap_collect_tick += 1

        if len(self.lap_log_dict['data']) > 0:
            self.generate_summary()
            self.clear_lap_data()

    def update_tick_dict(self):
        super().update_tick_dict()
        if self.ibt_file and not self.ibt_data:
            self.tick_dict['IsOnTrack'] = False

    def generate_summary(self):
        lap_ls = []
        time_ls = []
        fuel_ls = []

        for idx, data in enumerate(self.lap_log_dict['data']):
            if data:
                lap_ls.append(self.lap_log_dict['lap'][idx])
                time_ls.append(self.lap_log_dict['time'][idx])
                fuel_ls.append(self.lap_log_dict['fuel'][idx])

        if len(lap_ls) > 0:
            total_laps = len(lap_ls)

            fastest_time = min(time_ls)
            slowest_time = max(time_ls)
            mean_time = sum(time_ls) / total_laps
            fastest_delta = abs(fastest_time - mean_time)
            slowest_delta = abs(slowest_time - mean_time)

            fastest_str = get_time_str(fastest_time)
            mean_str = get_time_str(mean_time)
            slowest_str = get_time_str(slowest_time)
            fastest_delta_str = str(round(fastest_delta, 2))
            slowest_delta_str = str(round(slowest_delta, 2))

            total_fuel = sum(fuel_ls)
            mean_fuel = total_fuel / total_laps
            max_fuel = max(fuel_ls)
            min_fuel = min(fuel_ls)

            total_fuel_str = str(round(total_fuel, 2)) + "L"
            mean_fuel_str = str(round(mean_fuel, 2)) + "L"
            max_fuel_str = str(round(max_fuel, 2)) + "L"
            min_fuel_str = str(round(min_fuel, 2)) + "L"

            print(f"\n{total_laps} Laps completed:"
                  f"\n\tAverage time: {mean_str} "
                  f"\n\tFastest time: {fastest_str} (-{fastest_delta_str}s to average) "
                  f"\n\tSlowest time: {slowest_str} (+{slowest_delta_str}s to average) "
                  f"\n\t\t(exc. out lap)"
                  f"\n\n{total_fuel_str} of fuel used:"
                  f"\n\tAverage: {mean_fuel_str} / lap"
                  f"\n\tMinimum: {min_fuel_str} / lap"
                  f"\n\tMaximum: {max_fuel_str} / lap "
                  f"\n\t\t(exc. out lap)\n")
        else:
            print("\nNo summary data\n")

    def clear_lap_data(self):
        for key in self.lap_log_dict.keys():
            self.lap_log_dict[key] = []
