# Written by S. Mevawala, modified by D. Gitzel

# Implemented By: Michael Bentivegna & Simon Yoon
# Communication Networks Final 2022

import logging
import socket
import threading
import time
from textwrap import wrap
import channelsimulator
import utils
import sys

class Sender(object):

    def __init__(self, inbound_port=50006, outbound_port=50005, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.sndr_setup(timeout)
        self.simulator.rcvr_setup(timeout)

    def send(self, data):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


#Implemented Sender class
class MySender(Sender):

    def __init__(self):
        super(MySender, self).__init__()
    
    #Process checksum bytes
    def checksum(self, data):
        ch = 37
        value = 0
    
        data = bytearray(data)
        for ch in data:
            value = 37 * value + ch;
            value = value % 1e10
            
        value = int(value % 1e10)
        valueString = self.turnIntoString(value)

        return valueString

    #Change integer into 10 character string
    def turnIntoString(self, data):
        dataString = "0"*(10-len(str(data))) + str(data)
        return dataString

    #Send a packet with all proper information(data, seqNum, checksum)
    def send_packet(self, data, seq):
        seqString = self.turnIntoString(seq)
        check = self.checksum(data + seqString)
        self.simulator.u_send(bytearray(data + seqString + check))

    #Go-Back-N resend function
    def re_send(self, allPackets, baseGBN, maxPacket):
        for i in range(10):
            if baseGBN + i < maxPacket:
                self.send_packet(allPackets[baseGBN + i], baseGBN + i)
                self.logger.info("Resent packet {}".format(baseGBN + i))

    #Mission Control Sender
    def send(self, data):
        self.logger.info("Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))

        #Declarations
        timers = threading.Timer(1, True)
        timers.daemon = True 
        baseGBN = 0
        sequenceNum = 0
        N = 5;

        while True:

            #Split data into packets of proper length
            packets = [data[i:i+1004] for i in range(0, len(data), 1004)] 

            #Send packet and increment sequence number under these Go-Back-N parameters
            if ((sequenceNum < baseGBN + N) and (sequenceNum < len(packets))):
                self.send_packet(packets[sequenceNum], sequenceNum)
                self.logger.info("Sent packet {}".format(sequenceNum))
                sequenceNum = sequenceNum + 1

                #If sequence number caught up to the maximum value it can send start the timer
                if(baseGBN + N - 1 == sequenceNum):
                    timers = threading.Timer(.02, self.re_send, [packets, baseGBN, len(packets)])
                    timers.daemon = True 
                    timers.start()

                #Burst out the first N bytes for speed
                elif(sequenceNum < N):
                    continue
  
            try:
                #Attempt to receive Ack
                ack = self.simulator.u_receive()
                #self.logger.info("Received ack {}".format(ack))

                #If checksum matches process the ack, if not skip to next iteration
                if ack[-10:] == self.checksum(ack[:-10]):
                    self.logger.info("Received ack {}".format(ack[:-10]))
                    #If ack matches GBN value, this means the receiver has successfully received the packet
                    if (str(ack[:-10]) == self.turnIntoString(baseGBN)):
                        baseGBN = baseGBN + 1
                        timers.cancel()

                    #If the ack is greater than the GBN value, this means the recevier has gotten all packets up to that ack
                    elif (int(str(ack[:-10])) > baseGBN):
                        baseGBN = int(str(ack[:-10]));

                    #If the ack is less than the GBN, start timer for resend
                    else:
                        timers.cancel()
                        timers.join()
                        timers = threading.Timer(.02, self.re_send, [packets, baseGBN, len(packets)])
                        timers.daemon = True 
                        timers.start()
                
                #Corrupted ack so skip to next iteration
                else:
                    continue

                

            #End once no Acks are received anymore
            except:
                break
                       

if __name__ == "__main__":

    #Run send method with data file
    DATA = bytearray(sys.stdin.read())
    sndr = MySender()
    sndr.send(DATA)
