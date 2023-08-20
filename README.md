# Lap Logger tool

lap logging tool for iRacing based on pyirsdk. 
This tool can be used to understand lap time consistency or for back to back 
comparison of set-ups, fuel levels, fuel saving techniques, cars, in car 
settings etc.

## Usage
Run main.py and the tool will open in a python console window. On completion 
of each lap the lap time and fuel used will be printed to the console. On 
exiting the car a summary of lap times and fuel use will be added. Getting 
back into the car will start a new lap logging session in the same window.

The tool can also be run with an ibt telemetry file by specifying a file 
path for the ibt_file variable in main.py.  If the real_time_ibt variable
is set to true then the file will be processed in real time.

## Dependencies
pyirsdk plus python standard library modules (time).

## Extendability
This project is intended to be extensible and to provide a basis for 
further tools and projects through the use of it's DataLogger base class.
See notes in [base_class.py](base_class.py) for further details and
[lap_logger.py](lap_logger.py) for an example of a class that inherits
from this base class. 
