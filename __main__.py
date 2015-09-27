import RPi.GPIO as gpio
import threading
from time import sleep

gpio.setmode(gpio.BOARD)

gpio_in_doorbell = 37
gpio_in_lampoverride = 35
gpio_in_hornoverride = 33
gpio_in_printoverride = 31
gpio_in_confirm = 29

gpio_out_warninglamp = 40
gpio_out_horn = 38
gpio_out_led_doorbell = 36
gpio_out_led_confirm = 32

def setup_gpios():
    gpio.setup(gpio_in_doorbell, gpio.IN, pull_up_down=gpio.PUD_UP)
    gpio.setup(gpio_in_lampoverride, gpio.IN, pull_up_down=gpio.PUD_UP)#FIXME
    gpio.setup(gpio_in_hornoverride, gpio.IN, pull_up_down=gpio.PUD_UP)#FIXME
    gpio.setup(gpio_in_printoverride, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(gpio_in_confirm, gpio.IN, pull_up_down=gpio.PUD_DOWN)

    gpio.setup(gpio_out_warninglamp, gpio.OUT)
    gpio.setup(gpio_out_horn, gpio.OUT)
    gpio.setup(gpio_out_led_doorbell, gpio.OUT)
    gpio.setup(gpio_out_led_confirm, gpio.OUT)

def wait_for_confirmation():
    print('waiting for confirmation')
    def blink_confirm():
        gpio.add_event_detect(gpio_in_confirm, gpio.RISING, bouncetime=200)
        while not gpio.event_detected(gpio_in_confirm):
            gpio.output(gpio_out_led_confirm, True)
            sleep(500)
            gpio.output(gpio_out_led_confirm, False)
            sleep(500)
        gpio.remove_event_detect(gpio_in_confirm)
        confirmthread = threading.Thread(target=lambda: blink_confirm())
        confirmthread.start()
    gpio.wait_for_edge(gpio_in_confirm, gpio.RISING)
    print('got confirmation')


def run_warninglamp(time, confirm):
    print('run_warninglamp %s.'%time)
    if gpio.input(gpio_in_lampoverride):
        gpio.output(gpio_out_warninglamp, True)
        sleep(time)
        if confirm:
            wait_for_confirmation()
        gpio.output(gpio_out_warninglamp, False)
    print('ran warninglamp')

def sound_horn(pattern, time):
    #TODO
    pass

def eval_doorbell(channel):
    print('Edge detected on channel %s, eval_doorbell.'%channel)
#    gpio.output(gpio_out_led_doorbell, True)
    warninglampthread = threading.Thread(target=lambda: run_warninglamp(3, 0))
    warninglampthread.start()
#    gpio.wait_for_edge(gpio_in_doorbell, gpio.RISING)
#    gpio.output(gpio_out_led_doorbell, False)


def eval_phone():
    #TODO
    #while phone_ringing():
    #run_warninglamp(1)
    pass

setup_gpios()
gpio.add_event_detect(gpio_in_doorbell, gpio.FALLING, callback=eval_doorbell, bouncetime=200)
eval_doorbell(-1)#FIXME
while True:
    gpio.output(gpio_out_led_confirm, not gpio.input(gpio_in_doorbell))
    sleep(.1)

