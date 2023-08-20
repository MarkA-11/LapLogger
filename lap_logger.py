from base_class import DataLogger
from functions import get_time_str

"""
Example of a class that inherits from the DataLogger base class
"""


class LapLogger(DataLogger):

    def __init__(self, ibt_file=None, real_time_ibt=False):
        # a name and current version for our class
        name = "lap logger"
        version = "0.1"
        # logging lap completion so 1 sample / sec is sufficient but should be higher for real time telemetry
        sample_rate = 1
        # set up the keys for the data that we will want to access
        data_key_ls = ['IsOnTrack', 'Lap', 'LapCompleted', 'LapLastLapTime', 'FuelLevel']

        # ibt_file and real_time_ibt are arguments for this LapLogger class and these are passed directly to the base
        # class init function along with all the parameters for our class defined above
        super().__init__(name=name, version=version, data_key_ls=data_key_ls, sample_rate=sample_rate,
                         ibt_file=ibt_file, real_time_ibt=real_time_ibt)

        # set up some instance attributes that we will need
        # a dictionary to store the lap data in
        self.lap_log_dict = {'data': [],
                             'lap': [],
                             'time': [],
                             'fuel': []}
        # a maximum time in seconds to wait after lap completion before collecting the last lap time
        # collection usually happens when the last lap time changes but having a max wait takes care of a few edge
        # cases such as the first out lap in a session or (very unlikely) driving two identical lap times!
        self.max_collect_wait = 8

    def loop(self):
        # call the loop function in the base class to update the tick dict
        super().loop()

        # check if the car is on track with the driver in it
        if self.tick_dict['IsOnTrack']:
            # if it is then set up for lap logging
            # pause to let the laps complete value update settle
            self.wait(2)
            # update the tick_dict
            self.update_tick_dict()
            # set the session lap count to 0 and get the laps completed, last lap time
            session_lap = 0
            laps_complete = self.tick_dict['LapCompleted']
            last_lap_time = self.tick_dict['LapLastLapTime']
            # get the fuel level and print the starting fuel for the lap session to the console
            fuel_level = self.tick_dict['FuelLevel']
            start_fuel_str = str(round(fuel_level, 2)) + "L"
            print(f"\nStarting fuel {start_fuel_str}, Logging lap data.... \n")
            # set the lap time collection flag to false, work out what the max ticks before collecting the
            # last lap time should be for the defined sample rate and reset the associated tick counter
            collect_lap_time = False
            max_lap_collect_tick = self.max_collect_wait * self.sample_rate
            lap_collect_tick = 0

            # the while loop runs the lap logging session while the car is on track with the driver in it
            while self.tick_dict['IsOnTrack']:
                # need to update the tick_dict within this loop to get the latest data and to drop out of the loop
                # if the car is no longer on track
                self.update_tick_dict()
                # check if the lap completed value is different to what we have - indicating a lap has been completed
                if self.tick_dict['LapCompleted'] != laps_complete:
                    # updated our laps completed value
                    laps_complete = self.tick_dict['LapCompleted']
                    # append the session lap number to our session dictionary and then increment it
                    self.lap_log_dict['lap'].append(session_lap)
                    session_lap += 1
                    # last lap times update a little after lap completion to set the collect lap time flag
                    # so that the lat lap time gets collected when it changes
                    collect_lap_time = True
                    # append None to the other lists of the session dictionary as placeholder
                    self.lap_log_dict['data'].append(None)
                    self.lap_log_dict['time'].append(None)
                    # get the fuel used, append the value to the session dictionary and reset the fuel level value
                    fuel_used = round(fuel_level - self.tick_dict['FuelLevel'], 2)
                    self.lap_log_dict['fuel'].append(fuel_used)
                    fuel_level = self.tick_dict['FuelLevel']

                if collect_lap_time and \
                        (self.tick_dict['LapLastLapTime'] != last_lap_time or lap_collect_tick >= max_lap_collect_tick):
                    # if lap time is to be collected and either the last lap time has changed or the maximum
                    # collection wait (tick) has been exceeded then go ahead and collect it

                    # rest the values that control lap time collection
                    last_lap_time = self.tick_dict['LapLastLapTime']
                    collect_lap_time = False
                    lap_collect_tick = 0

                    # replace the placeholder in the session dictionary with the lap time value
                    self.lap_log_dict['time'][-1] = last_lap_time
                    # use the get_time_str function to see if there is a valid lap time and replace the placeholder
                    # in the session dictionary accordingly
                    if get_time_str(last_lap_time) != 'No data':
                        self.lap_log_dict['data'][-1] = True
                    else:
                        self.lap_log_dict['data'][-1] = False

                    # now that the lap time has been collected we can print the data for the last lap to the console
                    # make a string for this lap with the session lap, time and fuel used
                    lap_str = f"\tlap: {self.lap_log_dict['lap'][-1]} - " \
                              f"Time: {get_time_str(self.lap_log_dict['time'][-1])}, " \
                              f"Fuel: {self.lap_log_dict['fuel'][-1]}L"
                    # if the session lap was 0 then append out lap
                    if self.lap_log_dict['lap'][-1] == 0:
                        lap_str += " (out lap)"
                    print(lap_str)

                elif collect_lap_time:
                    # if a lap time is to be collected but has not been then increment the collection tick counter
                    lap_collect_tick += 1

        # once the while loop exits (car is no longer on track) check to see if there is data in the session dictionary
        if len(self.lap_log_dict['data']) > 0:
            # if there is then generate a summary and then clear the session dictionary
            self.generate_summary()
            self.clear_session_data()

    def update_tick_dict(self):
        # call the update tick_dict function in the base class
        super().update_tick_dict()
        # if there is no more data in the ibt file then set the IsOnTrack parameter to false so that the while loop
        # in the loop function drops out and goes to the generate summary stage
        if self.ibt_file and not self.ibt_data:
            self.tick_dict['IsOnTrack'] = False

    def generate_summary(self):
        # set up lists to hold the lap, time and fuel
        lap_ls = []
        time_ls = []
        fuel_ls = []

        # go through the data list in the session dictionary
        for idx, data in enumerate(self.lap_log_dict['data']):
            # this will be true for laps with valid data and false otherwise
            if data:
                # if there is data append the values it to the corresponding list
                lap_ls.append(self.lap_log_dict['lap'][idx])
                time_ls.append(self.lap_log_dict['time'][idx])
                fuel_ls.append(self.lap_log_dict['fuel'][idx])

        # check if there is at least one lap with valid data in the lists
        if len(lap_ls) > 0:
            # if there is then calculate various summary statistic values
            total_laps = len(lap_ls)
            fastest_time = min(time_ls)
            slowest_time = max(time_ls)
            mean_time = sum(time_ls) / total_laps
            fastest_delta = abs(fastest_time - mean_time)
            slowest_delta = abs(slowest_time - mean_time)
            total_fuel = sum(fuel_ls)
            mean_fuel = total_fuel / total_laps
            max_fuel = max(fuel_ls)
            min_fuel = min(fuel_ls)

            # turn the summary statistic values into strings
            fastest_str = get_time_str(fastest_time)
            mean_str = get_time_str(mean_time)
            slowest_str = get_time_str(slowest_time)
            fastest_delta_str = str(round(fastest_delta, 2))
            slowest_delta_str = str(round(slowest_delta, 2))
            total_fuel_str = str(round(total_fuel, 2)) + "L"
            mean_fuel_str = str(round(mean_fuel, 2)) + "L"
            max_fuel_str = str(round(max_fuel, 2)) + "L"
            min_fuel_str = str(round(min_fuel, 2)) + "L"

            # use the strings to print the summary to the console
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
            # if there are no valid laps in the lists then print no data
            print("\nNo summary data\n")

    def clear_session_data(self):
        # basic function to clear the session dictionary
        for key in self.lap_log_dict.keys():
            self.lap_log_dict[key] = []
