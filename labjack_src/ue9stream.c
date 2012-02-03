//Author: LabJack
//Oct. 3, 2007
//This example program reads analog inputs AI0 - AI3 (default) using stream mode

#include <signal.h>
#include "ue9.h"

char *ipAddress;
const int ue9_portA = 52360;
const int ue9_portB = 52361;
const int ainResolution = 14;
const int settlingTime = 0;
const int streamClockFreq = 4e6;
uint16 scanInterval = 4000;
uint8 NumChannels = 4;        // NumChannels needs to be 1, 2, 4, 8 or 16
int ALIVE = 1;

int StreamConfig(int socketFD);
int StreamStart(int socketFD);
int StreamData(int socketFDA, int socketFDB, ue9CalibrationInfo *caliInfo);
int StreamStop(int socketFDA, int displayError);
int flushStream(int socketFD);
int doFlush(int socketFDA);

void termination_handler(int signum)
{
    ALIVE = 0;
}

int main(int argc, char **argv)
{
    long now = getTickCount();
    int sampRate = 1000;
    int socketFDA, socketFDB;
    double runDurationSeconds = 0;
    ue9CalibrationInfo caliInfo;
    socketFDA = -1;
    socketFDB = -1;


    if(argc < 2)
    {
        printf("Please enter an ip address to connect to.\n");
        exit(0);
    }
    ipAddress = argv[1];
    if(argc > 2)
        sampRate = (int)atol(argv[2]);
    if(argc > 3)
        NumChannels = (uint8)atol(argv[3]);
    if(argc > 4)
        runDurationSeconds = atol(argv[4]);
    if(argc > 5)
    {
        printf("Too many arguments.\nPlease enter only an ip address, number of channels (1-4), sample rate (10 - 1000 Hz), and run duration (0 - 1e6 seconds, 0=infinity).\n");
        exit(0);
    }
    if(sampRate > 1000)
        sampRate = 1000;
    else if(sampRate<10)
        sampRate = 10;
    // Set the scanInterval
    // ScanInterval: (1-65535) This value divided by the clock frequency
    // gives the interval (in seconds) between scans.
    scanInterval = streamClockFreq/sampRate;
    //if(NumChannels>4)
    //    NumChannels = 4;
    //else if(NumChannels<1)
    //    NumChannels = 1;
    //else if(NumChannels==3)
    //    NumChannels = 4;
    if( (socketFDA = openTCPConnection(ipAddress, ue9_portA)) < 0)
        goto exit;

    doFlush(socketFDA);

    if( (socketFDB = openTCPConnection(ipAddress, ue9_portB)) < 0)
        goto close;

    if(getCalibrationInfo(socketFDA, &caliInfo) < 0)
        goto close;

    if(StreamConfig(socketFDA) != 0)
        goto close;

    signal(SIGTERM, termination_handler);

    if(StreamStart(socketFDA) != 0)
        goto close;

    long latency = getTickCount() - now;

    printf("prodID:                 %d\n", caliInfo.prodID);
    printf("unipolarSlope:          %f %f %f %f\n", caliInfo.unipolarSlope[0], caliInfo.unipolarSlope[1], caliInfo.unipolarSlope[2], caliInfo.unipolarSlope[3]);
    printf("unipolarOffset:         %f %f %f %f\n", caliInfo.unipolarOffset[0], caliInfo.unipolarOffset[1], caliInfo.unipolarOffset[2], caliInfo.unipolarOffset[3]);
    printf("bipolarSlope:           %f\n", caliInfo.bipolarSlope);
    printf("bipolarOffset:          %f\n", caliInfo.bipolarOffset);
    printf("DACSlope:               %f %f\n", caliInfo.DACSlope[0], caliInfo.DACSlope[1]);
    printf("DACOffset:              %f %f\n", caliInfo.DACOffset[0], caliInfo.DACOffset[1]);
    printf("tempSlope:              %f\n", caliInfo.tempSlope);
    printf("tempSlopeLow:           %f\n", caliInfo.tempSlopeLow);
    printf("calTemp:                %f\n", caliInfo.calTemp);
    printf("Vref:                   %f\n", caliInfo.Vref);
    printf("VrefDiv2:               %f\n", caliInfo.VrefDiv2);
    printf("VsSlope:                %f\n", caliInfo.VsSlope);
    printf("hiResUnipolarSlope:     %f\n", caliInfo.hiResUnipolarSlope);
    printf("hiResUnipolarOffset:    %f\n", caliInfo.hiResUnipolarOffset);
    printf("hiResBipolarSlope:      %f\n", caliInfo.hiResBipolarSlope);
    printf("hiResBipolarOffset:     %f\n", caliInfo.hiResBipolarOffset);
    printf("estimated latency [ms]: %ld\n", latency);
    printf("********************************************************************************\n");
    printf("\n\n");


    StreamData(socketFDA, socketFDB, &caliInfo);
    StreamStop(socketFDA, 1);

close:
    if(closeTCPConnection(socketFDA) < 0)
        printf("Error: failed to close socket (portA)\n");
    if(closeTCPConnection(socketFDB) < 0)
        printf("Error: failed to close socket (portB)\n");
exit:
    return 0;
}

//Sends a StreamConfig low-level command to configure the stream to read
//NumChannels analog inputs.
int StreamConfig(int socketFD)
{
    int sendBuffSize;
    uint8 *sendBuff;
    uint8 recBuff[8];
    int sendChars, recChars, i, ret;
    uint16 checksumTotal;

    sendBuffSize = 12 + 2*NumChannels;
    sendBuff = malloc(sizeof(uint8)*sendBuffSize);
    ret = 0;

    sendBuff[1] = (uint8)(0xF8);      //command byte
    sendBuff[2] = NumChannels + 3;    //number of data words : NumChannels + 3
    sendBuff[3] = (uint8)(0x11);      //extended command number
    sendBuff[6] = (uint8)NumChannels; //NumChannels
    sendBuff[7] = ainResolution;      //resolution
    sendBuff[8] = settlingTime;       //SettlingTime = 0
    sendBuff[9] = 0;                  //ScanConfig: scan pulse and external scan trigger disabled, stream clock frequency = 4 MHz

    sendBuff[10] = (uint8)(scanInterval & 0x00FF); //scan interval (low byte)
    sendBuff[11] = (uint8)(scanInterval / 256);	   //scan interval (high byte)

    for(i = 0; i < NumChannels; i++)
    {
        sendBuff[12 + i*2] = i; //channel # = i
        sendBuff[13 + i*2] = 0; //BipGain (Bip = unipolar, Gain = 1)
    }

    extendedChecksum(sendBuff, sendBuffSize);

    //Sending command to UE9
    sendChars = send(socketFD, sendBuff, sendBuffSize, 0);
    if(sendChars < 20)
    {
        if(sendChars == -1)
            printf("Error : send failed (StreamConfig)\n");
        else
            printf("Error : did not send all of the buffer (StreamConfig)\n");
        ret = -1;
        goto cleanmem;
    }

    //Receiving response from UE9
    recChars = recv(socketFD, recBuff, 8, 0);
    if(recChars < 8)
    {
        if(recChars == -1)
            printf("Error : receive failed (StreamConfig)\n");
        else
            printf("Error : did not receive all of the buffer (StreamConfig)\n");
        goto cleanmem;
    }

    checksumTotal = extendedChecksum16(recBuff, 8);
    if( (uint8)((checksumTotal / 256) & 0xff) != recBuff[5])
    {
        printf("Error : received buffer has bad checksum16(MSB) (StreamConfig)\n");
        ret = -1;
        goto cleanmem;
    }

    if( (uint8)(checksumTotal & 0xff) != recBuff[4])
    {
        printf("Error : received buffer has bad checksum16(LBS) (StreamConfig)\n");
        ret = -1;
        goto cleanmem;
    }

    if( extendedChecksum8(recBuff) != recBuff[0])
    {
        printf("Error : received buffer has bad checksum8 (StreamConfig)\n");
        ret = -1;
        goto cleanmem;
    }

    if( recBuff[1] != (uint8)(0xF8) || recBuff[2] != (uint8)(0x01) || recBuff[3] != (uint8)(0x11) || recBuff[7] != (uint8)(0x00))
    {
        printf("Error : received buffer has wrong command bytes (StreamConfig)\n");
        ret = -1;
        goto cleanmem;
    }

    if(recBuff[6] != 0)
    {
        printf("Errorcode # %d from StreamConfig received.\n", (unsigned int)recBuff[6]);
        ret = -1;
        goto cleanmem;
    }

cleanmem:
    free(sendBuff);
    sendBuff = NULL;

    return ret;
}

//Sends a StreamStart low-level command to start streaming.
int StreamStart(int socketFD)
{
    uint8 sendBuff[2], recBuff[4];
    int sendChars, recChars;

    sendBuff[0] = (uint8)(0xA8);  //CheckSum8
    sendBuff[1] = (uint8)(0xA8);  //command byte

    //Sending command to UE9
    sendChars = send(socketFD, sendBuff, 2, 0);
    if(sendChars < 2)
    {
        if(sendChars == -1)
            printf("Error : send failed\n");
        else
            printf("Error : did not send all of the buffer\n");
        return -1;
    }

    //Receiving response from UE9
    recChars = recv(socketFD, recBuff, 4, 0);
    if(recChars < 4)
    {
        if(recChars == -1)
            printf("Error : receive failed\n");
        else
            printf("Error : did not receive all of the buffer\n");
        return -1;
    }

    if( recBuff[1] != (uint8)(0xA9) || recBuff[3] != (uint8)(0x00) )
    {
        printf("Error : received buffer has wrong command bytes \n");
        return -1;
    }

    if(recBuff[2] != 0)
    {
        printf("Errorcode # %d from StreamStart received.\n", (unsigned int)recBuff[2]);
        return -1;
    }

    return 0;
}

//Reads the StreamData low-level function response in a loop.  All voltages from
//the stream are stored in the voltages 2D array.
int StreamData(int socketFDA, int socketFDB, ue9CalibrationInfo *caliInfo)
{
    uint8 *recBuff;
    double **voltages;
    int recChars, backLog, overflow, totalScans, ret;
    int i, k, m, packetCounter, currChannel, scanNumber;
    int totalPackets;        //The total number of StreamData responses read
    uint16 voltageBytes, checksumTotal;


    int numDisplay;          //Number of times to display streaming information
    int numScansPerStreamBundle;  //Multiplier for the StreamData receive buffer size
    long startTime, endTime;

    unsigned long int curScanNum = 0;

    packetCounter = 0;

    totalPackets = 0;
    recChars = 0;
    numScansPerStreamBundle = 10;
    ret = 0;

    recBuff = malloc(sizeof(uint8)*46*numScansPerStreamBundle);

    while(ALIVE)
    {
        /* You can read the multiple StreamData responses of 46 bytes to help
         * improve throughput.  In this example this multiple is adjusted by the
         * numScansPerStreamBundle variable.  We may not read 46 * numScansPerStreamBundle
         * bytes per each recv call, but we will continue reading until we read
         * 46 * numScansPerStreamBundle bytes total.
         */
        recChars = 0;
        for(k = 0; k < 46*numScansPerStreamBundle; k += recChars)
        {
            //Reading response from UE9
            recChars = recv(socketFDB, recBuff + k, 46*numScansPerStreamBundle - k, 0);
            if(recChars == 0)
            {
                printf("Error : read failed (StreamData).\n");
                ret = -1;
            }
        }

        overflow = 0;

        //Checking for errors and getting data out of each StreamData response
        for (m = 0; m < numScansPerStreamBundle; m++)
        {
            checksumTotal = extendedChecksum16(recBuff + m*46, 46);
            if( (uint8)((checksumTotal / 256) & 0xff) != recBuff[m*46 + 5])
            {
                printf("Error : read buffer has bad checksum16(MSB) (StreamData).\n");
                ret = -1;
            }

            if( (uint8)(checksumTotal & 0xff) != recBuff[m*46 + 4])
            {
                printf("Error : read buffer has bad checksum16(LBS) (StreamData).\n");
                ret = -1;
            }

            checksumTotal = extendedChecksum8(recBuff + m*46);
            if( checksumTotal != recBuff[m*46])
            {
                printf("Error : read buffer has bad checksum8 (StreamData).\n");
                ret = -1;
            }

            if( recBuff[m*46 + 1] != (uint8)(0xF9) || recBuff[m*46 + 2] != (uint8)(0x14) || recBuff[m*46 + 3] != (uint8)(0xC0) )
            {
                printf("Error : read buffer has wrong command bytes (StreamData).\n");
                ret = -1;
            }

            if(recBuff[m*46 + 11] != 0)
            {
                printf("Errorcode # %d from StreamData read.\n", (unsigned int)recBuff[11]);
                ret = -1;
            }

            curScanNum += packetCounter-(int)recBuff[m*46 + 10]+1;
            if(packetCounter != (int)recBuff[m*46 + 10])
            {
                printf("PacketCounter (%d) does not match with with current packet count (%d) (StreamData).\n", packetCounter, (int)recBuff[m*46 + 10]);
                packetCounter = (int)recBuff[m*46 + 10];
                ret = -1;
            }

            backLog = recBuff[m*46 + 45] & 0x7F;

            //Checking MSB for Comm buffer overflow
            if( (recBuff[m*46 + 45] & 128) == 128)
            {
                printf("\nComm buffer overflow detected in packet %d\n", totalPackets);
                printf("Current Comm backlog: %d\n", recBuff[m*46 + 45] & 0x7F);
                overflow = 1;
            }

            // uint32 timeStamp = *(uint32*)(recBuff+m*46+6);

            // The data packet structure:
            // Byte		
            // 0     Checksum8	
            // 1     0xF9	
            // 2     0x14	
            // 3     0xC0	
            // 4     Checksum16 (LSB)	
            // 5     Checksum16 (MSB)	
            // 6-9   TimeStamp ("Reserved"- seems not to be used yet- it's always zero.)	
            // 10    PacketCounter	
            // 11    Errorcode	
            // 12-13 Sample0	
            // 14-15 Sample1	
            // ...
            // 40-41 Sample14	
            // 42-43 Sample15	
            // 44    ControlBacklog	
            // 45    CommBacklog
            int offset = 12; // Offset to current ADC value
            int numReadsPerScan = 16/NumChannels;
            for(i=0; i<numReadsPerScan; i++)
            {
                printf("%10ld, ", curScanNum*numReadsPerScan+i);
                for(k=0; k<NumChannels; k++)
                {
                    double voltage;
                    voltageBytes = (uint16)recBuff[m*46 + offset] + (uint16)recBuff[m*46 + offset+1] * 256;
                    binaryToCalibratedAnalogVoltage(caliInfo, (uint8)(0x00), ainResolution, voltageBytes, &voltage);
                    printf("%11.8f, %5d,  ", voltage, voltageBytes);
                    offset+=2;
                }
                printf("\n");
            }

            if(packetCounter >= 255)
                packetCounter = 0;
            else
                packetCounter++;

            //Handle Comm buffer overflow by stopping, flushing and restarting stream
            if(overflow == 1)
            {
                printf("\nRestarting stream...\n");

                doFlush(socketFDA);
                closeTCPConnection(socketFDB);

                if( (socketFDB = openTCPConnection(ipAddress, ue9_portB)) < 0)
                {
                    printf("Error re-opening socket.\n");
                    ret = -1;
                }
                if(StreamConfig(socketFDA) != 0)
                {
                    printf("Error restarting StreamConfig.\n");
                    ret = -1;
                }

                if(StreamStart(socketFDA) != 0)
                {
                    printf("Error restarting StreamStart.\n");
                    ret = -1;
                }
                packetCounter = 0;
                break;
            }
        }
    }

    free(recBuff);
    recBuff = NULL;
    return ret;
}

//Sends a StreamStop low-level command to stop streaming.
int StreamStop(int socketFD, int displayError)
{
    uint8 sendBuff[2], recBuff[4];
    int sendChars, recChars;

    sendBuff[0] = (uint8)(0xB0);  //CheckSum8
    sendBuff[1] = (uint8)(0xB0);  //command byte

    sendChars = send(socketFD, sendBuff, 2, 0);
    if(sendChars < 2)
    {
        if(displayError)
        {
            if(sendChars == -1)
                printf("Error : send failed (StreamStop)\n");
            else
                printf("Error : did not send all of the buffer (StreamStop)\n");
            return -1;
        }
    }

    //Receiving response from UE9
    recChars = recv(socketFD, recBuff, 4, 0);
    if(recChars < 4)
    {
        if(displayError)
        {
            if(recChars == -1)
                printf("Error : receive failed (StreamStop)\n");
            else
                printf("Error : did not receive all of the buffer (StreamStop)\n");
        }
        return -1;
    }

    if( recBuff[1] != (uint8)(0xB1) || recBuff[3] != (uint8)(0x00) )
    {
        if(displayError)
            printf("Error : received buffer has wrong command bytes (StreamStop)\n");
        return -1;
    }

    if(recBuff[2] != 0)
    {
        if(displayError)
            printf("Errorcode # %d from StreamStop received.\n", (unsigned int)recBuff[2]);
        return -1;
    }

    return 0;
}

//Sends a FlushBuffer low-level command to clear the stream buffer.
int flushStream(int socketFD)
{
    uint8 sendBuff[2], recBuff[2];
    int sendChars, recChars;

    sendBuff[0] = (uint8)(0x08);  //CheckSum8
    sendBuff[1] = (uint8)(0x08);  //command byte

    //Sending command to UE9
    sendChars = send(socketFD, sendBuff, 2, 0);
    if(sendChars < 2)
    {
        if(sendChars == -1)
            printf("Error : send failed (flushStream)\n");
        else
            printf("Error : did not send all of the buffer (flushStream)\n");
        return -1;
    }

    //Receiving response from UE9
    recChars = recv(socketFD, recBuff, 4, 0);
    if(recChars < 2)
    {
        if(recChars == -1)
            printf("Error : receive failed (flushStream)\n");
        else
            printf("Error : did not receive all of the buffer (flushStream)\n");
        return -1;
    }

    if(recBuff[0] != (uint8)(0x08) || recBuff[1] != (uint8)(0x08))
    {
        printf("Error : received buffer has wrong command bytes (flushStream)\n");
        return -1;
    }
    return 0;
}

//Runs StreamStop and flushStream low-level functions to flush out the streaming
//buffer.  This function is useful for stopping streaming and clearing it after
//a Comm buffer overflow.
int doFlush(int socketFDA)
{
    //printf("Flushing stream.\n");
    StreamStop(socketFDA, 0);
    flushStream(socketFDA);

    return 0;
}
