# from heatcontroller import HeatController
from controlcontroller import ControlController
import os

# (1) Change sensor type here
from sensor import MCP9808

# (2) Change sensor type here
# List representation for use if the system will
# contain multiple types of temperature sensors.

# Signify the temperature sensor that will
# not be averaged as an indoor reading
# This may be different on each system
# due to inconsistent naming/numbering.

excluded_sensor = "1D"

# List of reserved i2c addresses
# that are used by components
# other than temperature sensors.
# Make sure that each of the elements
# in this list are hexadecimal strings
# i.e. "1a".
reserved = ["68"]

# You must include a Python implementation that
# uses the Sensor superclass for the
# type of sensor in your system (see sensor.py)
sensor = [MCP9808(reserved)]

# Find the USB folder in the mount point
path = "/media/pi/"
directory = os.listdir(path)
path = path + directory[0] + "/"

# Initialize the controller program
tent_control = ControlController(path, sensor, excluded_sensor)

# Enter the main control loop
tent_control.main()
