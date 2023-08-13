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
        self.data_key_ls = data_key_ls
        self.data_dict = {}
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

        # turn this into a function that returns a dict ?
        # save referencing self.data_dict every time in the loop of the inheriting class!
        self.ir.freeze_var_buffer_latest()
        for data_key in self.data_key_ls:
            self.data_dict[data_key] = self.ir[data_key]
        # need to check if this is needed but doesn't seem to hurt
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

        # replace this with a counter / collector class ?
        # alternatively do all this when last lap time changes ? very unlikely to be the same to 13 decimal places!
        collect_delay_tgt_secs = 2  # seconds to wait before collecting the last lap time
        self.collect_delay_tgt = collect_delay_tgt_secs*self.sample_rate
        self.collect_lap_time = False
        self.collect_delay_count = 0

    def event_activated(self):
        super().event_activated()
        self.laps_complete = self.ir['Lap']
        self.session_lap = 0
        self.add_start_data()
        self.add_header()

    def event_deactivated(self):
        print("\n")
        self.generate_summary()
        self.export_data()
        print("Stopping lap logging session")
        super().event_deactivated()

    def loop(self):
        super().loop()

        # if a new lap has been completed then trigger delayed collection of the lap time
        # (last lap time updates a little after the car crosses the line)
        if self.data_dict['Lap'] > self.laps_complete:
            self.laps_complete = self.data_dict['Lap']
            # set the lap time collect flag and reset the counter
            self.collect_lap_time = True
            self.collect_delay_count = 0

        # if waiting to collect a lap time and target delay has been reached then get the lap time str
        if self.collect_lap_time and self.collect_delay_count >= self.collect_delay_tgt:
            # reset the collect flag and the counter
            self.collect_lap_time = False
            self.collect_delay_count = 0
            # get the last lap time as a string and print it
            last_lap_time_str = get_laptime_str(self.data_dict['LapLastLapTime'])
            print(f"Lap {str(self.session_lap)}:\t{last_lap_time_str}")
            # increment logging session lap number (after printing lap_time_str so that 0 is the out lap)
            self.session_lap += 1
        # if waiting to collect a lap time and target delay not reached increment the counter
        elif self.collect_lap_time:
            self.collect_delay_count += 1

    def add_start_data(self):
        if self.ir['WeekendInfo']['TrackDisplayName']:
            track_info_str = str(self.ir['WeekendInfo']['TrackDisplayName'])
            if self.ir['WeekendInfo']['TrackConfigName']:
                track_info_str = track_info_str + " - " + str(self.ir['WeekendInfo']['TrackConfigName'])
        else:
            track_info_str = ''
        if self.ir['WeekendInfo']['TrackSurfaceTemp']:
            track_temp_str = f"Track temp:{self.ir['WeekendInfo']['TrackSurfaceTemp']}"
        else:
            track_temp_str = ''
        start_fuel_str = f"Starting fuel: {str(round(self.ir['FuelLevel'], 2))}L"
        start_str = "\nStarting lap logging session.."+"\n"+track_info_str+"\n"+track_temp_str+"\n"+start_fuel_str+"\n"
        print(start_str)

    def add_header(self):
        header_str = "Session lap times:\n"
        print(header_str)

    def generate_summary(self):
        print("place holder text for session summary")

    def export_data(self):
        date_time_str = datetime.now().strftime("%d-%m-%y_%H-%M-%S")+".txt"
        if self.ir['WeekendInfo']['TrackName']:
            track_name_str = self.ir['WeekendInfo']['TrackName'].replace(' ', '_')
        else:
            track_name_str = ''
        file_name_str = track_name_str+"_"+date_time_str
        print(f"exporting data to {file_name_str} (not implemented in {self.version})")
        # need to check this - causes a crash on first use / if lap logger running before iracing ?
        # with open(file_name_str, 'w') as file:
        #    file.write('placeholder file for session data export')
