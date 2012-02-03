#!/usr/bin/env python

import sys
import socket
from datetime import datetime
import subprocess
import signal
import os
import time
import serial

# Be sure to set this to the correct device! Under linux, it is something
# like /dev/ttyACM0. On OSX, it will be /dev/ttyUSBNNNN, where NNNN is
# some cryptic number. On windows, it will be a COM port (e.g., COM4).
TRIGGER_DEVICE = '/dev/ttyACM0'
LABJACK_HOSTNAME = '10.0.3.1'

class LabjackRunner:
    """
    lj = LabjackRunner(outfilename)
    lj.start()  # returns immediately
    # wait a while, then...
    lj.stop()   # halt recording and close the output file

    """

    def __init__(self, outfilename, hostname = '10.0.3.1', sampRate = 100):
        self.hostname = hostname
        self.outfile_name = outfilename
        self.outfile_desc = None
        self.hostip = socket.gethostbyname(self.hostname)
        self.lj_proc = None
        self.sampleRate = sampRate

    def start(self):
        self.outfile_desc = open(self.outfile_name,'w')
        timeRef = datetime.now()
        self.outfile_desc.write('%% Start time: %s\n' % str(timeRef))
        self.outfile_desc.flush()
        self.lj_proc = subprocess.Popen(['./ue9stream', self.hostip, str(self.sampleRate)], stdout = self.outfile_desc, cwd = os.getcwd())
        # subprocess.communicate to hang until it finishes

    def stop(self):
        self.lj_proc.terminate()
        self.lj_proc = None
        # flush stdout
        self.outfile_desc.close()
        self.outfile_desc = None

RUNNING = True

def handler(signum, frame):
    global RUNNING
    RUNNING = False

# Set the signal handler to allow clean exit with a TERM signal
signal.signal(signal.SIGTERM, handler)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = time.strftime('biopac_%Y%m%d_%H%M%S.csv')

    if len(sys.argv) > 2:
    	runDuration = float(sys.argv[2])
    else:
        runDuration = 0.0

    if runDuration>0:
        print "Will record to %s for %0.2f seconds." % (filename, runDuration)
    else:
        print "Will record to %s forever (or until you hit ctrl-c)." % filename

    lj = LabjackRunner(filename, LABJACK_HOSTNAME)

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

    lj.start()  # returns immediately
    startSecs = time.time()
    while RUNNING:
        try:
            time.sleep(0.1)  # a caught signal (like TERM) will abort the sleep
        except:
            RUNNING = False
        if runDuration>0 and time.time()-startSecs>=runDuration:
            RUNNING = False
    lj.stop()   # halt recording and close the output file
    print "Finished recording."


