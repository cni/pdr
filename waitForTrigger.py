#!/usr/bin/env python

import sys
import socket
from datetime import datetime
import signal
import os
import time
import serial

# Be sure to set this to the correct device! Under linux, it is something
# like /dev/ttyACM0. On OSX, it will be /dev/ttyUSBNNNN, where NNNN is
# some cryptic number. On windows, it will be a COM port (e.g., COM4).
TRIGGER_DEVICE = '/dev/ttyACM0'

RUNNING = True

def handler(signum, frame):
    global RUNNING
    RUNNING = False

# Set the signal handler to allow clean exit with a TERM signal
signal.signal(signal.SIGTERM, handler)

if __name__ == "__main__":

    try:
        ser = serial.Serial(TRIGGER_DEVICE, 115200, timeout=0.1)
        # Allow time for trigger device to initialize:
        time.sleep(0.1)
        # Send a trigger pulse to start scanning
        #ser.write('[t]\n');
        # Display the firmware greeting
        out = ser.readlines()
        for l in out: print(l),
        # Send the command to enable input pulses
        ser.write('[p]\n');

        print "Waiting for trigger..."
        # Wait for a scan trigger to start (or a ctrl-c)
        waiting = True
        while waiting and RUNNING:
            n = ser.inWaiting()
            # Wait for a char, or until timeout
            if n>0:
                s = ser.read(n)
                if s[0]=='p':
                    waiting = False
            else:
                time.sleep(0.01)
        RUNNING = True
    except:
        print "No trigger device found."

    print "Starting recording now"


