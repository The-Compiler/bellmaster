import RPi.GPIO as gpio
from time import sleep
from twisted.internet import reactor, protocol
import re


gpio.setmode(gpio.BOARD)

gpio_in_doorbell = 37
gpio_in_lampoverride = 33
gpio_in_beeperoverride = 31
gpio_in_printoverride = 29
gpio_in_confirm = 29

gpio_out_warninglamp = 40
gpio_out_beeper = 38
gpio_out_led_doorbell = 36
gpio_out_led_confirm = 32


def SetupGpios():
    gpio.setup(gpio_in_doorbell, gpio.IN, pull_up_down = gpio.PUD_UP)
    gpio.setup(gpio_in_lampoverride, gpio.IN, pull_up_down = gpio.PUD_DOWN)
    gpio.setup(gpio_in_beeperoverride, gpio.IN, pull_up_down = gpio.PUD_DOWN)
    gpio.setup(gpio_in_printoverride, gpio.IN, pull_up_down = gpio.PUD_DOWN)
    gpio.setup(gpio_in_confirm, gpio.IN, pull_up_down = gpio.PUD_DOWN)
    
    gpio.setup(gpio_out_warninglamp, gpio.OUT)
    gpio.setup(gpio_out_beeper, gpio.OUT)
    gpio.setup(gpio_out_led_doorbell, gpio.OUT)
    gpio.setup(gpio_out_led_confirm, gpio.OUT)


class OutputController:
    def __init__(self, gpio_pin_id):
        self._current_output_state = False
        self._current_reasons = set()
        
        self._gpio_pin_id = gpio_pin_id
    
    def _check_output(self):
        print 'checking output'
        print 'self._current_output_state', self._current_output_state, 'self._current_reasons', self._current_reasons
        if self._current_output_state and not self._current_reasons:
            print 'setting output to False'
            self._set_output(False)
        elif not self._current_output_state and self._current_reasons:
            print 'setting output to True'
            self._set_output(True)



    def _set_output(self, state):
        gpio.output(self._gpio_pin_id, state)
    
    def addReason(self, reason):
        print 'adding reason ', reason
        self._current_reasons.add(reason)
        self._check_output()
    
    def removeReason(self, reason):
        print 'removing reason', reason
        self._current_reasons.remove(reason)
        self._check_output()


lampOutputController = OutputController(gpio_out_warninglamp)
beeperOutputController = OutputController(gpio_out_beeper)


def handleCall(call_id):
    print 'handling call with id ', call_id
    lampOutputController.addReason(('call', call_id))
    sleep(5)
    lampOutputController.removeReason(('call', call_id))


class fritzClient(protocol.Protocol):
    def connectionMade(self):
        print "connected to fritz.hq.ccczh.ch"
    
    def dataReceived(self, data):
        data = data.strip()
        data_split = re.split(";", data)
        action = data_split[1]
        action_handlers = {
            "CALL": self._handleCall,
            "RING": self._handleRing,
            "DISCONNECT": self._handleDisconnect,
            "CONNECT": self._handleConnect,
        }
        try:
            func = action_handlers[action]
        except KeyError:
            return
        func()
    
    def connectionLost(self, reason):
        print "connection lost", reason
    
    def _handleCall(self):
        pass
    
    def _handleRing(self):
        pass
    
    def _handleDisconnect(self):
        pass
    
    def _handleConnect(self):
        pass


class FritzFactory(protocol.ClientFactory):
    protocol = fritzClient
    
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - reconnecting", reason
        connect_to_fritzbox()
    
    def clientConnectionLost(self, connector, reason):
        print "Connection lost - reconnecting", reason
        connect_to_fritzbox()


def connect_to_fritzbox(f):
    print 'initiating connection with fritz.hq.ccczh.ch'
    reactor.connectTCP("fritz.hq.ccczh.ch", 1012, f)



def handleDoorbell():
    lampOutputController.addReason('doorbell')

    def _turnOffLamp():
        lampOutputController.removeReason('doorbell')

    reactor.callLater(10, _turnOffLamp)


def evalDoorbell(channel):
    print('Edge detected on channel %s, eval_doorbell.' % channel)
    pcRuns = 0
    pcFalseScore = 0
    while pcRuns < 10:
        if gpio.input(channel):
            pcFalseScore += 1
        pcRuns += 1
    if pcFalseScore > 5:
        print('Signal on channel %s did not pass primitive positive-confirmation.' % channel)
    else:
        reactor.callFromThread(handleDoorbell)


SetupGpios()
gpio.add_event_detect(gpio_in_doorbell, gpio.FALLING, callback = evalDoorbell, bouncetime = 1)
f = FritzFactory()
connect_to_fritzbox(f)
reactor.run()
