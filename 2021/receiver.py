# Written by S. Mevawala, modified by D. Gitzel

# Implemented By: Michael Bentivegna & Simon Yoon
# Communication Networks Final 2022

import logging
import channelsimulator
import utils
import sys
import socket

class Receiver(object):

    def __init__(self, inbound_port=50005, outbound_port=50006, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.rcvr_setup(timeout)
        self.simulator.sndr_setup(timeout)

    def receive(self):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class MyReceiver(Receiver):

    def __init__(self):
        super(MyReceiver, self).__init__()

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

    #Mission control Receiever
    def receive(self):
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))

        #Declarations
        ack = 0

        while True:

            #Attempt to receive data packet
            try:
                data = self.simulator.u_receive()

                #Check if corrupted
                if self.checksum(data[:-10]) == data[-10:]:

                    #See if ack received matches the expected ack
                    if(data[-20:-10] == self.turnIntoString(ack)):            
                        
                        #Write to output file
                        sys.stdout.write(data[0:len(data)-20])
                        
                        #Send ack with checksum packet & increment
                        checkAck = self.checksum(str(data[-20:-10]))
                        packetAck = str(data[-20:-10]) + checkAck
                        self.simulator.u_send(bytearray(packetAck))

                        self.logger.info("Sent Ack {}".format(ack))
                        ack = ack + 1
                    
                    #If data is from different packet then expected, send ack - 1 packet
                    else:
                        #Make ack and checksum into packet
                        prevAck = self.turnIntoString(ack - 1)
                        prevAckCheck = self.checksum(prevAck)

                        #Send packet
                        self.simulator.u_send(bytearray(prevAck + prevAckCheck))
                        self.logger.info("Sent Ack duplicate {}".format(ack))

                #If corrupted go to next iteration
                else:
                    continue

            except socket.timeout:
                sys.exit()

if __name__ == "__main__":
    #Start implemented receiver
    rcvr = MyReceiver()
    rcvr.receive()
