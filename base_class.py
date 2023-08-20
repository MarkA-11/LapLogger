import irsdk
import time

"""
  DataLogger is the base class, any classes that inherit from this will work with the main.py function
  and have the base functionality described below, see lap_logger for an example of a class that inherits 
  from this base class.

  Class can run connected to the sim or from an ibt file, an ibt file can be played back in
  real time by setting real_time_ibt true.
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
