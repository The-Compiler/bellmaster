from twisted.internet import reactor, protocol
import re

class EchoClient(protocol.Protocol):
    """Once connected, send a message, then print the result."""

    def connectionMade(self):
        self.transport.write("hello, world!")
        print "connected"

    def dataReceived(self, data):
        data = data.strip()
        data_split = re.split(";",data)
        action = data_split[1]
        action_handlers = {
            "CALL": self.handle_call,
            "RING": self.handle_ring,
            "DISCONNECT": self.handle_disconnect
        }
        try:
            func = action_handlers[action]
        except KeyError:
            return
        func()

    def connectionLost(self, reason):
        print "connection lost", reason

    def handle_call(self):
        pass

    def handle_ring(self):
        self.ringing =  True
        gpio.output(gpio_out_warninglamp, True)
        return

    def handle_disconnect(self):
        if self.ringing:
            gpio.output(gpio_out_warninglamp, False)
        return

class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!", reason
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!", reason
        reactor.stop()


# this connects the protocol to the local fritzbox
def main():
    f = EchoFactory()
    reactor.connectTCP("fritz.hq.ccczh.ch", 1012, f)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    import RPi.GPIO as gpio
    gpio.setmode(gpio.BOARD)
    gpio_out_warninglamp = 40
    gpio.setup(gpio_out_warninglamp, gpio.OUT)
    main()
