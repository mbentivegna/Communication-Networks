# Written by S. Mevawala, modified by D. Gitzel

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


class BogoReceiver(Receiver):

    def __init__(self):
        super(BogoReceiver, self).__init__()

    def receive(self):
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        ack = 0

        while True:
            try:
                data = self.simulator.u_receive()  # receive data
                
                if(data[-10:] == "0"*(10-len(str(ack))) + str(ack)):            
                    self.simulator.u_send("0"*(10-len(str(ack))) + str(ack))  # send ACK
                    sys.stdout.write(data[0:len(data)-10])
                    ack = ack + 1
                    self.logger.info("Sent Ack {}".format(ack))
                else:
                    self.simulator.u_send("0"*(10-len(str(ack-1))) + str(ack-1))
                    self.logger.info("Sent Ack duplicate{}".format(ack))

                #self.logger.info("Got data from socket: {}".format(
                    #data.decode()))  # note that ASCII will only decode bytes in the range 0-127

            except socket.timeout:
                sys.exit()

if __name__ == "__main__":
    # test out BogoReceiver
    rcvr = BogoReceiver()
    rcvr.receive()
