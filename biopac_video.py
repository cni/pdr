#!/usr/bin/env python

import sys
import socket
from datetime import datetime
import subprocess
import shlex
import signal
import os
import time
import serial


# Be sure to set this to the correct device! Under linux, it is something
# like /dev/ttyACM0. On OSX, it will be /dev/ttyUSBNNNN, where NNNN is
# some cryptic number. On windows, it will be a COM port (e.g., COM4).
TRIGGER_DEVICE = '/dev/ttyACM0'
LABJACK_HOSTNAME = '192.168.0.12'
FFMPEG = 'ffmpeg -f video4linux2 -i /dev/video0 -t %d -vcodec libx264 %s'

class FfmpegRunner:
    """
    ff = FfmpegRunner(outfilename)
    ff.start()  # returns immediately
    # wait a while, then...
    ff.stop()   # halt recording and close the output file
    """
    def __init__(self, outfilename, duration):
        self.outfile_name = outfilename
        self.outfile_desc = None
        self.proc = None
        self.duration = duration

    def start(self):
        self.outfile_desc = open('/tmp/biopac_video.log','w')
        self.ff_proc = subprocess.Popen(shlex.split(FFMPEG % (self.duration, self.outfile_name)), stdout=self.outfile_desc, cwd=os.getcwd())
        # subprocess.communicate to hang until it finishes

    def stop(self):
        if self.proc != None:
            self.proc.terminate()
            self.proc = None
        # close the log file
        if self.outfile_desc != None:
            self.outfile_desc.close()
            self.outfile_desc = None

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
        self.proc = None
        self.sampleRate = sampRate

    def start(self):
        self.outfile_desc = open(self.outfile_name,'w')
        timeRef = datetime.now()
        self.outfile_desc.write('%% Start time: %s\n' % str(timeRef))
        self.outfile_desc.flush()
        self.proc = subprocess.Popen(['ue9stream', self.hostip, str(self.sampleRate)], stdout=self.outfile_desc, cwd=os.getcwd())
        # subprocess.communicate to hang until it finishes

    def stop(self):
        if self.proc != None:
            self.proc.terminate()
            self.proc = None
        # flush stdout
        if self.outfile_desc != None:
            self.outfile_desc.close()
            self.outfile_desc = None

RUNNING = True

def handler(signum, frame):
    global RUNNING
    RUNNING = False

# Set the signal handler to allow clean exit with a TERM signal
signal.signal(signal.SIGTERM, handler)

if __name__ == "__main__":
    runDuration = float(sys.argv[1])
    try:
        ser = serial.Serial(TRIGGER_DEVICE, 115200, timeout=0.1)
        # Allow time for trigger device to initialize:
        time.sleep(0.1)
        # Send a trigger pulse to start scanning
        #ser.write('[t]\n');
        out = ser.readlines()
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
    except:
        print('skipping trigger.')
    RUNNING = True

    ts = time.strftime('%Y%m%d_%H%M%S')
    lj_fname = '/home/cni/biopac/physio_' + ts + '.csv'
    ff_fname = '/home/cni/video/subvid_' + ts + '.mp4'

    print "Recording to %s and %s for %0.2f minutes..." % (lj_fname, ff_fname, runDuration/60.)

    lj = LabjackRunner(lj_fname, LABJACK_HOSTNAME)
    ff = FfmpegRunner(ff_fname, runDuration)
    lj.start()  # returns immediately
    ff.start()  # returns immediately
    startSecs = time.time()
    while RUNNING:
        try:
            time.sleep(0.1)  # a caught signal (like TERM) will abort the sleep
        except:
            RUNNING = False
        if runDuration>0 and time.time()-startSecs>=runDuration:
            RUNNING = False
    lj.stop()   # halt recording and close the output file
    ff.stop()   # halt recording and close the output file
    print "Finished recording."


