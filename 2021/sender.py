# Written by S. Mevawala, modified by D. Gitzel

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


class BogoSender(Sender):

    def __init__(self):
        super(BogoSender, self).__init__()
        
    
    

    def checksum(self, preprocessedData):
        sequenceNum = 1

    def make_packet(self, data):
        sequenceNum = 2

    def resend(self, allPackets, baseGBN, maxPacket):
        for i in range(10):
            if baseGBN + i < maxPacket:
                self.simulator.u_send(bytearray(allPackets[baseGBN + i]) + bytearray("0"*(10-len(str(baseGBN + i))) + str(baseGBN + i)))
                self.logger.info("Resent packet {}".format(baseGBN + i))

    def send(self, data):
        self.logger.info("Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))

        timers = threading.Timer(1, True)
        timers.daemon = True 
        baseGBN = 0
        sequenceNum = 0
        N = 10;
        n = 0;

        while True:

            packets = [data[i:i+1014] for i in range(0, len(data), 1014)] 

            if ((sequenceNum < baseGBN + N) and (sequenceNum < len(packets))):
                self.simulator.u_send(bytearray(packets[sequenceNum]) + bytearray("0"*(10-len(str(sequenceNum))) + str(sequenceNum)))
                self.logger.info("Sent packet {}".format(sequenceNum))
                sequenceNum = sequenceNum + 1
                if(baseGBN + N - 1 == sequenceNum):
                    timers = threading.Timer(.02, self.resend, [packets, baseGBN, len(packets)])
                    timers.daemon = True 
                    timers.start()
                elif(sequenceNum < N):
                    continue

                    
            try:
                ack = self.simulator.u_receive()
                self.logger.info("Received ack {}".format(ack))
             
                if (ack == "0"*(10-len(str(baseGBN))) + str(baseGBN)):
                    self.logger.info("GBN {}".format(baseGBN))
                    baseGBN = baseGBN + 1
                    timers.cancel()
                elif (int(str(ack)) > baseGBN):
                    baseGBN = int(str(ack));
                    self.logger.info("GBN Boosted Up {}".format(baseGBN))
                else:
                    self.logger.info("GBN too high {}".format(baseGBN))
                    timers.cancel()
                    timers.join()
                    timers = threading.Timer(.02, self.resend, [packets, baseGBN, len(packets)])
                    timers.daemon = True 
                    timers.start()

            except:
                sys.exit()        

if __name__ == "__main__":
    # test out BogoSender
    DATA = bytearray(sys.stdin.read())
    sndr = BogoSender()
    sndr.send(DATA)
