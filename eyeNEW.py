#!/usr/bin/env python

import socket
import sys
import datetime
import time
import serial
import json
import string

class EyeTrackReceiver:
    """
    Implements a receiver for the Arrington Research eye tracker TCP data stream.
    Example:
        import eye
        et = eye.EyeTrackReceiver('cnitrack.stanford.edu',5000)
        # To save data for 3 minutes:
        et.saveDataTimed('dataFile.txt', 60*3)
        # Or, to go into command processing mode:
        import time
        et.startCommandPort('/dev/ttyUSB0')
        while 1:
            et.processCommands()
            time.sleep(0.1)
    """

    def __init__(self, host = 'cnitrack.stanford.edu', port = 5000, verbose = False, logFile = None, dataDir = './'):
        self.host = host
        self.port = port
        self.sock = None
        self.outfile = None
        self.verbose = verbose
        self.marker = None
        self.commandDevice = None
        self.inPulseDevice = None
        self.logFile = logFile
        self.savingData = False
        self.commandDeviceBuffer = ''
        self.dataDir = dataDir

    def connect(self):
        if self.sock != None:
            self.sock.close()
            self.sock = None
        for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
            except socket.error, msg:
                self.sock = None
                continue
            try:
                self.sock.connect(sa)
            except socket.error, msg:
                self.sock.close()
                self.sock = None
            continue
            break
        if self.sock is None:
            print 'could not open socket'
            sys.exit(1)
        else:
            print "Setting socket timeout."
            self.sock.settimeout(5)

    def disconnect(self):
        self.sock.close()
        self.sock = None

    def startCommandPort(self, device = '/dev/ttyUSB0'):
        self.commandDevice = serial.Serial(device, 115200, timeout=1)

    def startInPulse(self, device = '/dev/ttyACM0'):
        self.inPulseDevice = serial.Serial(device, 115200, timeout=1)
        # Send the command to enable pulses
        self.inPulseDevice.write('[p]\n');
        # Display the firmware greeting
        out = self.inPulseDevice.readlines()
        if self.verbose:
            for l in out: print(l),

    def checkInPulse(self):
        n = self.inPulseDevice.inWaiting()
        if n>0:
            s = self.inPulseDevice.read(n)
        if s[0]=='p':
            pulsed = True
        else:
            pulsed = False
        return pulsed

    def waitInPulse(self):
        # Use select.select here for a better way to block.
        while not self.checkInPulse():
            time.sleep(0.05)

    def processCommands(self):
        # E.g., record to a file called "Series3" for 1 minute:
        # {"dev":"eye","cmd":"start","dur":60,"file":"test.csv"}
        # To send a marker:
        # {"dev":"eye","cmd":"mark","val":"this is my marker, damnit!"}
        if self.commandDevice != None:
            n = self.commandDevice.inWaiting()
        else:
            n = 0
        if n>0:
            self.commandDeviceBuffer = self.commandDeviceBuffer + self.commandDevice.read(n)
        # *** TODO: better string parsing!
        endOfCmd = string.find(self.commandDeviceBuffer, '}')
        if endOfCmd != -1:
            s = self.commandDeviceBuffer[0:endOfCmd+1]
            self.commandDeviceBuffer = self.commandDeviceBuffer[endOfCmd+2:]
            if self.verbose:
                self.logMessage('Processing command: '+s+'.')
            try:
                d = json.loads(s)
            except:
                self.logMessage('Invalid JSON: "'+s+'".')
                d = None
            if d!=None and d.has_key('cmd'):
                cmd = d['cmd']
                if cmd == 'start':
                    if d.has_key('dur'):
                        duration = d['dur']
                    else:
                        duration = 3600
                    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    if d.has_key('file'):
                        fileName = self.dataDir+d['file']+'_'+ts+'.csv'
                    else:
                        fileName = self.dataDir+'eye_'+ts+'.csv'
                    #if not self.savingData:
                    self.logMessage('Saving eyetracker data to file '+fileName+' '+str(duration)+'.')
                    self.marker = None
                    self.saveDataTimed(fileName, duration)
                    self.logMessage('Finished saving '+fileName+'.')
                    #else:
                    #    self.logMessage('Already saving data!')
                elif cmd == 'stop':
                    self.logMessage('Received stop command- ending recording.')
                    self.savingData = False
                elif cmd == 'mark' and d.has_key('val'):
                    self.marker = d['val']
                    self.logMessage('Setting marker to "'+self.marker+'".')
                else:
                    self.logMessage('Invalid command: "'+s+'".')
        return

    def logMessage(self, msg):
        if self.logFile != None:
            self.logFile.write(time.asctime()+': Eye: '+msg+'\n')
            self.logFile.flush()
            print msg
        else:
            print msg
        return

    def getCurMarker(self):
        self.processCommands()
        # return the current marker
        marker = self.marker
        # Should we reset it to None? No, we'll keep the old marker until we get a new one.
        #self.marker = None
        return marker

    def openFile(self, name = None, append=False):
        if name == None:
            name = time.strftime('%Y%m%d_%H%M%S.txt')
        if name == '-':
            self.outfile = sys.stdout
        else:
            if append==True:
                self.outfile = open(name, 'a')
            else:
                self.outfile = open(name, 'w')
        # *** ERROR CHECKING HERE ***

    def closeFile(self):
        if self.outfile != sys.stdout:
            self.outfile.close()

    def getDataPacket(self):
        packetSize = 0
        while packetSize==0:
            if self.sock.recv(1)=='V' and self.sock.recv(3)=='PX2':
                packetSize = int(self.sock.recv(12)[:-2])
            else:
                if self.verbose:
                    self.outfile.write('BAD PACKET\n')
        packet = self.sock.recv(packetSize+10)
        # Parse the data packet. I wish there was a prettier way to do this!
        data = packet.rsplit(';')
        for i in range(10):
            data[i] = data[i][2:]
        for i in range(10,27):
            data[i] = data[i][3:]
        return data

    def printHeader(self):
        nowTs = time.time()
        self.outfile.write('3\tCustomer Serial Number:  200-1035-1-1\n')
        self.outfile.write('3\tCustomer Name:  CNI\n')
        self.outfile.write('3\tCustomer Organization:  Stanford University\n')
        self.outfile.write('3\t--------------------------------------------------------\n')
        self.outfile.write(datetime.datetime.utcfromtimestamp(nowTs).strftime('3\tTimeValues\t%Y\t%m\t%d\t%H\t%M\t%S\tUTC\n'))
        self.outfile.write(datetime.datetime.fromtimestamp(nowTs).strftime('3\tTimeStamp\t%A, %B %d, %Y, %I:%M:%S %p\n'))
        self.outfile.write('3\tDataFormat\t2.8.4,523\n')
        self.outfile.write('3\tStoring UN-SMOOTHED data.\n')
        self.outfile.write('3\tScreenSize\t124.878\t93.5065\n')
        self.outfile.write('3\tViewingDistance\t500\n')
        self.outfile.write('3\tImageShape\tFit\n')
        self.outfile.write('3\t--------------------------------------------------------\n')
        self.outfile.write('3\t idName\n')
        self.outfile.write('3\t idTest\n')
        self.outfile.write('3\t idSession\n')
        self.outfile.write('3\t idNotes\n')
        self.outfile.write('3\t--------------------------------------------------------\n')
        self.outfile.write('6\tATT\tADT\tALX\tALY\tARI\tAPW\tAPH\tAQU\tAFX\tCNT\tMRK\n')
        self.outfile.write('5\tTotalTime\tDeltaTime\tX_Gaze\tY_Gaze\tRegion\tPupilWidth\tPupilHeight\tQuality\tFixation\tCount\tMarker\n')
        self.outfile.write('7\t0.000000\tEyeA FrameRate\t0\n')
        self.outfile.write('7\t0.000000\tEyeB FrameRate\t0\n')
        self.outfile.write('16\t0.000000\tSTARTUP.BMP\n')

    def saveDataTimed(self, fileName, numSeconds, append = True):
        # sock.send('Hello, world')
        # Might be better to keep the connection open and just clear the
        # input buffer here. But there is no simple way to clear the buffer, so
        # for now, we'll just do the connect here.
        self.savingData = True
        self.connect()
        startSecs = time.time()
        self.openFile(fileName, append)
        self.printHeader()
        # get the first data packet
        d = self.getDataPacket()
        #startSecs = float(d[5])
        totalTime = 0.0
        while totalTime <= numSeconds and self.savingData:
            # Write a line of data
            curSecs = time.time()
            deltaTime = curSecs - startSecs - totalTime
            totalTime = curSecs - startSecs
            gaze = d[10].rsplit(',')
            pupil = d[14].rsplit(',')
            # Check to see if there's a marker in the marker queue
            marker = self.getCurMarker()
            self.outfile.write('10\t%0.4f\t%0.4f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'
                    % (totalTime, deltaTime*1000, gaze[0], gaze[1], pupil[0], pupil[1], d[7], d[8], d[9], d[15], marker))
            self.outfile.flush()
            if self.verbose:
                for i in range(26):
                    sys.stdout.write('%s\t' % d[i])
                sys.stdout.write('\n')
                #print 'frame start:         %s' % d[3]
                #print 'frame duration:      %s' % d[4]
                #print 'frame end:           %s' % d[5]
                #print 'frame rate:          %s' % d[6]
                #print 'position:            %s' % d[10][3:]
                #print 'position:            %s' % d[11][3:]
                #print 'pupil major, minor:  %s' % d[14]
            d = self.getDataPacket()
        self.closeFile()
        self.disconnect()
        self.savingData = False



if __name__ == "__main__":
    eyeHost = 'cnitrack.stanford.edu'
    eyePort = 5000
    verbose = False
    duration = 0
    cniComPortDev = '/dev/ttyUSB0'

    dataFileName = 'eye.csv'
    if len(sys.argv)>=2:
        dataFileName = sys.argv[1]
    if len(sys.argv)>=3:
        duration = sys.argv[2]
    if len(sys.argv)>4:
        sys.exit(1)
    logFileName = 'nimspdr.log'

    with open(logFileName, 'a') as f:
        et = EyeTrackReceiver(host=eyeHost, port=eyePort, verbose=verbose, logFile=f)
        et.logMessage('%s *** NIMSPDR started ***\n' % time.asctime())
        if duration>0:
            et.saveDataTimed(dataFileName, duration)
        else:
            # Or, to go into command processing mode:
            et.startCommandPort(cniComPortDev)
            while running:
                et.processCommands()
                time.sleep(0.1)
        et.logMessage('%s: Received TERM, shutting down...\n' % time.asctime())
    print 'Shutting down.'
    exit(0)

