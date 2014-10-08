#!/usr/bin/env python

import sys
import socket
from datetime import datetime
import subprocess
import signal
import os
import time
import serial

import eye

# Be sure to set this to the correct device! Under linux, it is something
# like /dev/ttyACM0. On OSX, it will be /dev/ttyUSBNNNN, where NNNN is
# some cryptic number. On windows, it will be a COM port (e.g., COM4).
TRIGGER_DEVICE = '/dev/ttyACM0'
LABJACK_HOSTNAME = '192.168.0.12'
EYEHOST = 'cnitrack.stanford.edu'
EYEPORT = 5000

class LabjackRunner:
    """
    lj = LabjackRunner(outfilename)
    lj.start()  # returns immediately
    # wait a while, then...
    lj.stop()   # halt recording and close the output file

    """

    def __init__(self, outfilename, hostname=LABJACK_HOSTNAME, sampRate=100):
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
        self.lj_proc = subprocess.Popen(['ue9stream', self.hostip, str(self.sampleRate)], stdout = self.outfile_desc, cwd = os.getcwd())
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

    if len(sys.argv) < 2:
        sys.exit(1)

    runDuration = float(sys.argv[1])

    if len(sys.argv) > 2:
        biopac_filename = sys.argv[2]+time.strftime('physio_%Y%m%d_%H%M%S.csv')
        eye_filename = sys.argv[2]+time.strftime('eye_%Y%m%d_%H%M%S.csv')
    else:
        biopac_filename = '/home/cni/biopac/'+time.strftime('physio_%Y%m%d_%H%M%S.csv')
        eye_filename = '/home/cni/eye/'+time.strftime('eye_%Y%m%d_%H%M%S.csv')

    if runDuration>0:
        print "Will record to %s and %s for %0.2f seconds." % (biopac_filename, eye_filename, runDuration)
    else:
        print "Will record to %s forever (or until you hit ctrl-c)." % filename

    lj = LabjackRunner(biopac_filename, LABJACK_HOSTNAME)
    et = eye.EyeTrackReceiver(host=EYEHOST, port=EYEPORT)

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
    et.saveDataTimed(eye_filename, runDuration)
    lj.stop()   # halt recording and close the output file
    print "Finished recording."


