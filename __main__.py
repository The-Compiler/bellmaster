import RPi.GPIO as gpio
from time import sleep
from twisted.internet import reactor, protocol
import re


gpio.setmode(gpio.BOARD)

gpio_in_doorbell = 37
gpio_in_lampenable = 33
gpio_in_beeperenable = 31
gpio_in_printenable = 29
gpio_in_confirm = 29

gpio_out_warninglamp = 40
gpio_out_beeper = 38
gpio_out_led_doorbell = 36
gpio_out_led_confirm = 32


def SetupGpios():
    gpio.setup(gpio_in_doorbell, gpio.IN, pull_up_down = gpio.PUD_UP)
    gpio.setup(gpio_in_lampenable, gpio.IN, pull_up_down = gpio.PUD_DOWN)
    gpio.setup(gpio_in_beeperenable, gpio.IN, pull_up_down = gpio.PUD_DOWN)
    gpio.setup(gpio_in_printenable, gpio.IN, pull_up_down = gpio.PUD_DOWN)
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
        self._shouldBeOn = False
        self.enabled = True
    
    def check_output(self):
        print 'checking output'

        self._shouldBeOn = self._current_reasons and self.enabled

        print 'self._current_output_state', self._current_output_state, 'self._current_reasons', self._current_reasons, 'self._shouldBeOn', self._shouldBeOn

        if self._current_output_state and not self._shouldBeOn:
            print 'setting output to False'
            self._set_output(False)
        elif not self._current_output_state and self._shouldBeOn:
            print 'setting output to True'
            self._set_output(True)



    def _set_output(self, state):
        gpio.output(self._gpio_pin_id, state)
        self._current_output_state = state
    
    def addReason(self, reason):
        print 'adding reason ', reason
        self._current_reasons.add(reason)
        self.check_output()
    
    def removeReason(self, reason):
        print 'removing reason', reason
        self._current_reasons.remove(reason)
        self.check_output()

    def setEnable(self, state):
        self.enabled = state
        self.check_output()


lampOutputController = OutputController(gpio_out_warninglamp)
beeperOutputController = OutputController(gpio_out_beeper)


def handleCall(connectionId, action):
    print 'handling call with id ', connectionId, '. Action:', action
    if action == 'RING':
        lampOutputController.addReason(('call', connectionId))
    elif action == 'DISCONNECT' or 'CONNECT':
        print 'trying to remove call', connectionId, 'from reasons'
        try:
            lampOutputController.removeReason(('call', connectionId))
        except KeyError:
            print 'Warning: could not remove call ', connectionId, 'from reasons. (action=', action, ')'
    else:
        pass



class fritzClient(protocol.Protocol):

    def connectionMade(self):
        print "connected to fritz.hq.ccczh.ch"
    
    def dataReceived(self, data):
        data = data.strip()
        data_split = re.split(";", data)
        action = data_split[1]
        connectionId = data_split[2]
        handleCall(connectionId, action)


    def connectionLost(self, reason):
        print "connection lost", reason


class FritzFactory(protocol.ClientFactory):
    protocol = fritzClient
    
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - reconnecting", reason
        connectToFritzbox()
    
    def clientConnectionLost(self, connector, reason):
        print "Connection lost - reconnecting", reason
        connectToFritzbox()


def connectToFritzbox(f):
    print 'initiating connection with fritz.hq.ccczh.ch'
    reactor.connectTCP("fritz.hq.ccczh.ch", 1012, f)



def handleDoorbell():
    lampOutputController.addReason('doorbell')
    beeperOutputController.addReason('doorbell')

    def _turnOffLamp():
        lampOutputController.removeReason('doorbell')
    def _turnOffBeeper():
        beeperOutputController.removeReason('doorbell')

    reactor.callLater(5, _turnOffBeeper)
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
        print('Signal on channel %s did not pass primitive positive-confirmation-checking.' % channel)
    else:
        reactor.callFromThread(handleDoorbell)


def checkLampEnable(channel):
    print('detected edge on channel %s, checkLampEnable' % channel )
    sleep(.01)
    _state = gpio.input(gpio_in_lampenable)
    print 'trying lampOutputController.setEnable(', _state, ')'
    lampOutputController.setEnable(_state)


def checkBeeperEnable(channel):
    print('detected edge on channel %s, checkBeeperEnable' % channel)
    sleep(.01)
    _state = gpio.input(gpio_in_beeperenable)
    print 'trying beeperOutputController.setEnable(', _state, ')'
    beeperOutputController.setEnable(_state)


SetupGpios()
gpio.add_event_detect(gpio_in_doorbell, gpio.FALLING, callback = evalDoorbell, bouncetime = 1)

gpio.add_event_detect(gpio_in_lampenable, gpio.BOTH, callback = checkLampEnable, bouncetime = 1)
gpio.add_event_detect(gpio_in_beeperenable, gpio.BOTH, callback = checkBeeperEnable, bouncetime = 1)

f = FritzFactory()
connectToFritzbox(f)
reactor.run()
