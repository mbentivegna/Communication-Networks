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

    def receive(self):
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        ack = 0

        while True:


            try:
                data = self.simulator.u_receive()
                check = data[-10:]
                comp = self.checksum(data[:-10])
                if comp != check:
                    self.logger.info("Corrupted checksum{}".format(check))
                    self.logger.info("Corrupted seq {}".format(comp))
                    continue


                if(data[-20:-10] == "0"*(10-len(str(ack))) + str(ack)):            



                    sys.stdout.write(data[0:len(data)-20])



                    check = self.checksum(str(data[-20:-10]))
                    packet = str(data[-20:-10]) + check
                    self.simulator.u_send(bytearray(packet))  # send ACK
                    ack = ack + 1

                    self.logger.info("Sent Ack {}".format(ack))

                else:

                    tmp = ack-1
                    tmp = str(tmp)
                    tmp = "0"*(10-len(tmp)) + tmp
                    check = self.checksum(tmp)
                    self.simulator.u_send(bytearray(tmp+check))
                    self.logger.info("Sent Ack duplicate{}".format(ack))



            except socket.timeout:
                sys.exit()

if __name__ == "__main__":
    # test out BogoReceiver
    rcvr = BogoReceiver()
    rcvr.receive()
