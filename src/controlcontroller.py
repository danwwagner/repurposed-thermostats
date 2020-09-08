#!/usr/bin/env python

# Sensor Reading Author: Adafruit Foundation
# Source: https://bit.ly/1iFB8ZP (DS18B20)
# Adapted and modified by: Dan Wagner
# Agronomy Research, 2018-2019

import logging
import sys
import time
import codecs
import subprocess
import string
from shutil import copyfile


class ControlController:
    """
    Controller class that manages the Thermostat system
    """
    def __init__(self, data_dir, sensor_list):
        """
        Initializes the controller's variables and list of sensors.
        """

        # Designate the type of sensor we are using.
        self.sensors = sensor_list

        # Temperature value for the control sensor
        self.control_reading = 0

        # Keep track of the number of each type of sensors connected.
        self.num_sensors = [None] * len(self.sensors)

        # Filename for specific tent to write data
        self.data_file = '/home/pi/R1G1sensors.csv'

        self.dest_dirs = data_dir

        # Format for logging information
        self.format = "%(asctime)-15s %(message)s"

        # Temperature checking interval, in seconds
        self.check_interval = 300

        # List of sensors connected to the system
        self.sensor_list = []

        # Initialize the self.indoor temperature
        self.indoor = 0

        # Initialize self.heater status to OFF
        self.heater = "OFF"

        # Delimit the next day's individual sensor readings via blank line
        self.sensor_readings = codecs.open(self.data_file, 'a', 'utf-8')
        self.sensor_readings.write('\n')
        self.sensor_readings.close()

        # Instantiate the logging for debugging purposes
        self.logger = logging.getLogger("Controller")

        # Rcord the number of recent I/O errors
        self.io_errors = ''

        # Record number of reboots the system has experienced
        self.reboots = ''

        # Maximum number of allowable reboots
        self.reboot_max = 5

        # Maximum number of allowable I2C errors before reboot
        self.error_max = 3

    # Main loop of the program.
    def main(self):

        """
        Configure the logger and record the types of
        sensors that have been detected by the controller.
        """

	timer = subprocess.Popen('hwclock -s', stdout=subprocess.PIPE,
				 shell=True)

        self.logger.basicConfig = logging.basicConfig(format=self.format, 
                                                      filename='control.log',
                                                      level=logging.INFO)

        self.logger.info('SYSTEM ONLINE')

        # Log the types of sensors we have detected in the system
        for sen in self.sensors:
            self.logger.info('Detected %s sensors', str(sen))

        while True:
            # Detect the sensors that are currently connected
            for i in range(0, len(self.sensors)):
                try:
                    self.sensors[i].detect()
                    self.num_sensors[i] = self.sensors[i].num_sensors
                except IOError:
                    self.logger.info('Error detecting %s sensors',
                                     str(self.sensors[i]))

            try:
                # Open the sensor readings file and write current timestamp.
                self.logger.info('Opening sensors file for records')
                self.sensor_readings = codecs.open(self.data_file, 'a', 'utf-8')
                self.sensor_readings.write(time.strftime("%Y/%m/%d %H:%M:%S",
                                                         time.localtime()))

                # Read sensor data from all types of connected sensors.
                self.logger.info('Reading sensors from Pi')
                total_indoor = 0
                total_readings = ""
                error_flag = 0
                io_flag = 0
                for i in range(0, len(self.sensors)):
                    try:
                        self.indoor, readings, self.control_reading = self.sensors[i].read()
                        total_indoor += self.indoor
                        total_readings += readings
                    except (IOError, ZeroDivisionError):
                        self.logger.info('Error reading a sensor.')
                        error_flag += 1
                        io_flag = 1
                        # Read in error and reboot values for updates
                        self.io_errors = codecs.open('io_error', 'r', 'utf-8')
                        num_errors = int(self.io_errors.read())
                        self.io_errors.close()
                        self.reboots = codecs.open('reboots', 'r', 'utf-8')
                        num_reboots = int(self.reboots.read())
                        self.reboots.close()
                        # If maximum reboots not reached, then reboot
                        if (num_errors >= self.error_max and
                           num_reboots < self.reboot_max):
                            self.logger.info('Maximum I/O errors (%d);' +
                                             ' rebooting.', num_errors)
                            self.io_errors = codecs.open('io_error',
                                                         'w')
                            num_reboots += 1
                            self.io_errors.write('0')
                            self.io_errors.close()
                            self.reboots = codecs.open('reboots', 'w')
                            self.reboots.write((str(num_reboots)))
                            self.reboots.close()
                            self.sensor_readings.close()
                            proc = subprocess.Popen('reboot',
                                                    stdout=subprocess.PIPE,
                                                    shell=True)
                            out, err = proc.communicate()

                        # If maximum reboots reached, stay on
                        elif num_reboots == self.reboot_max:
                            num_errors += 1
                            self.logger.info('Max reboots (%d) reached;' +
                                             ' I/O error #%d occurred',
                                             num_reboots, num_errors)
                            self.io_errors = codecs.open('io_error',
                                                         'w')
                            self.io_errors.write((str(num_errors)))
                            self.io_errors.close()

                        # If maximums not reached, record the error
                        elif (num_reboots < self.reboot_max and
                              num_errors < self.error_max):
                            num_errors += 1
                            self.logger.info('I/O Error #%d occurred',
                                             num_errors)
                            self.io_errors = codecs.open('io_error'
                                                         ,'w')
                            self.io_errors.write((str(num_errors)))
                            self.io_errors.close()
            
                # No I/O error detected this time -> reset counters
                if not io_flag:
                    self.logger.info('No I/O error detected; ' +
                                     'resetting number of errors and reboots')
                    self.io_errors = codecs.open('io_error', 'w')
                    self.io_errors.write('0')
                    self.io_errors.close()
                    self.reboots = codecs.open('reboots', 'w')
                    self.reboots.write('0')
                    self.reboots.close()

                    self.indoor = total_indoor / len(self.sensors)
                    self.logger.info('Detected indoor temp of %.2f',
                                     self.indoor)

                # Round to three decimal places
                self.indoor = round(self.indoor, 3)

                if self.indoor == 0:
                    # sensors disconnected while running
                    raise RuntimeError

            except RuntimeError as ex:
                # Exception occurred with sensors
                self.indoor = 90
                self.heater = "SENSOR"

                # Record exception information
                self.logger.info('%s', repr(sys.exc_info()))
                print((str(ex)))

            # Immediately record outdoor temperature to file for control
            self.logger.info('Control: %d outside', self.indoor)

            self.logger.info('Recording temperature data to tent file %s',
                             self.data_file)

            # Remove non-printable characters (NULL, etc) and first comma
            outdoor_record = "".join(temp for temp in total_readings[1:] if temp in string.printable)
            if self.indoor != 90:
                try:
                    self.sensor_readings.write("," + repr(outdoor_record))
                    self.sensor_readings.write(",")
                    self.sensor_readings.write(str(self.control_reading))
                    self.sensor_readings.write("\n")
                    self.sensor_readings.close()
                        
                except: # Back up subsequent readings to the microSD
                    self.data_file = "/home/pi/sensors.csv"
                    self.output_file = codecs.open(self.data_file, 'a', 'utf-8')
                    self.output_file.write("," + repr(outdoor_record))
                    self.output_file.write(",")
                    self.output_file.write(str(self.control_reading))
                    self.output_file.write("\n")
                    self.output_file.close()

                # Copy over the data file to each "mounted" USB
                for dir in self.dest_dirs:
                    try:
                        copyfile(self.data_file, dir)
                    except:
                        continue
            else:
                self.logger.info('Cannot read sensors. No temperature data.')

            time.sleep(self.check_interval)
