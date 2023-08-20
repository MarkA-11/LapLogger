import irsdk
import time

"""
DataLogger is the base class. Any classes that inherit from this will work with the main.py function
and have the base functionality described below, see lap_logger.py for an example of a class that inherits 
from this base class.

    The check_connection function will determine if a running sim is currently connected (or if an ibt file is to be 
    played back and if data is available from it - see below) and set the connected variable accordingly.
    
    main.py will execute the classes loop function while connected to a running sim (or whilst playing back an ibt file 
    - see below) with data collected at the defined sample rate (max 60 samples/sec). The keys of the data to be 
    collected are defined in the data_key_ls variable and the loop function in the base class updates the tick_dict 
    variable with the latest sample ready to work with. The data sample can then be accessed in the loop function 
    via the keys of the tick_dict.
    
    The loop function can be utilised in two different ways: The code can effectively be executed while the sim is 
    connected by treating the loop function as a single run through. Alternatively, code can be executed while a 
    particular condition within the data itself is met. For example, The loop function within the LapLogger class 
    uses a while loop to run a lap logging session while the IsOnTrack parameter is true. 
    
    The update_tick_dict function will wait for the sample interval and then update the tick_dict with the latest data 
    sample from a running sim (or what would be the next data sample for the defined sample rate from an ibt file 
    - see below). 
    
    The update_tick_dict function uses the base class's wait function and it is important that this is used for any
    pauses as this will ensure that the next sample is taken from the ibt file correctly and also enable real time ibt 
    playback as described below.  
    
This class can run connected to the sim or from a specified ibt file, an ibt file can also effectively be played back 
in real time (with the defined sample rate) by setting real_time_ibt to true. This also allows for development and 
testing without the sim running but it is important to note that some parameters available from the ibt file 
may not be available from the running sim and vice versa. 

    A list of variables available from a running sim can be obtained by creating an instance of the pyirsdk IRSDK 
    class, calling the startup function with a .bin test file and printing the the var_headers_names parameter.
    
    The pyirsdk IBT class typically does not include the session info parameters available from the sim. Consequently
    these will not be available when the class is running with an ibt file. However, since these vary between session 
    types, tracks, cars etc anyway, it is best practice to check if they exist first before trying to access them in 
    any code.
"""


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
