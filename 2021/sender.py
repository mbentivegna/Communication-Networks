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
        
    
    def checksum(self, data):
        ch = 37
        value = 0
    
        data = bytearray(data)
        for ch in data:
            value = 37 * value + ch;
            value = value%1e10
            
        tmp = int(value % 1e10)
        tmp = str(tmp)
        tmp = "0"*(10-len(tmp)) + tmp

        return tmp





    def send_packet(self, data, seq):
        tmp = str(seq)
        tmp = "0"*(10-len(tmp)) + tmp
        check = self.checksum(data+tmp)
        self.simulator.u_send(bytearray(data) + bytearray(tmp + check, encoding="utf8"))






    def resend(self, allPackets, baseGBN, maxPacket):
        for i in range(10):
            if baseGBN + i < maxPacket:
                self.send_packet(allPackets[baseGBN + i], baseGBN + i)
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

            packets = [data[i:i+1004] for i in range(0, len(data), 1004)] 

            if ((sequenceNum < baseGBN + N) and (sequenceNum < len(packets))):
                self.send_packet(packets[sequenceNum], sequenceNum)
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

                check = ack[-10:]
                comp = self.checksum(ack[:-10])



                if check != comp:
                    self.logger.info("Corrupted checksum sender {}".format(check))
                    self.logger.info("Corrupted ack sender {}".format(comp))
                    continue


                if (str(ack[:-10]) == "0"*(10-len(str(baseGBN))) + str(baseGBN)):
                    self.logger.info("GBN {}".format(baseGBN))
                    baseGBN = baseGBN + 1
                    timers.cancel()
                elif (int(str(ack[:-10])) > baseGBN):
                    baseGBN = int(str(ack[:-10]));
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
