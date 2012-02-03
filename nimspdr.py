#!/usr/bin/env python
import eye
import sys, signal, time

# Be sure to set this to the correct device! Under linux, it is something
# like /dev/ttyACM0. On OSX, it will be /dev/ttyUSBNNNN, where NNNN is
# some cryptic number. On windows, it will be a COM port (e.g., COM4).
cniPhysMonDev = '/dev/ttyACM0'
cniComPortDev = '/dev/ttyUSB0'
eyeHost = 'cnitrack.stanford.edu'
eyePort = 5000
dataDir = '/home/cni/eye/'

verbose = False

running = True

def handler(signum, frame):
    global running
    running = False

# Set the signal handler to allow clean exit with a TERM signal
signal.signal(signal.SIGTERM, handler)
signal.signal(signal.SIGINT, handler)

if __name__ == "__main__":
    if len(sys.argv)==1:
        logfilename = dataDir+'nimspdr.log'
    elif len(sys.argv)==2:
        logfilename = sys.argv[1]
    else:
        sys.exit(1)

    with open(logfilename, 'a') as f:
        et = eye.EyeTrackReceiver(eyeHost,eyePort,verbose,f,dataDir)
        et.logMessage('%s *** NIMSPDR started ***\n' % time.asctime())
        # To save data for 3 minutes:
        #et.saveDataTimed('dataFile.txt', 60*3)
        # Or, to go into command processing mode:
        et.startCommandPort(cniComPortDev)
        while running:
            et.processCommands()
            time.sleep(0.1)
        et.logMessage('%s: Received TERM, shutting down...\n' % time.asctime())
    print 'Shutting down.'
    exit(0)

