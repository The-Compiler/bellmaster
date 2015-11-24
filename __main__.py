import RPi.GPIO as gpio
import threading
from time import sleep
import fritzlamp

gpio.setmode(gpio.BOARD)

gpio_in_doorbell = 37
gpio_in_lampoverride = 33
gpio_in_belloverride = 31
gpio_in_printoverride = 29
gpio_in_confirm = 29

gpio_out_warninglamp = 40
gpio_out_bell = 38
gpio_out_led_doorbell = 36
gpio_out_led_confirm = 32

def setup_gpios():
    gpio.setup(gpio_in_doorbell, gpio.IN, pull_up_down=gpio.PUD_UP)
    gpio.setup(gpio_in_lampoverride, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(gpio_in_belloverride, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(gpio_in_printoverride, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(gpio_in_confirm, gpio.IN, pull_up_down=gpio.PUD_DOWN)

    gpio.setup(gpio_out_warninglamp, gpio.OUT)
    gpio.setup(gpio_out_bell, gpio.OUT)
    gpio.setup(gpio_out_led_doorbell, gpio.OUT)
    gpio.setup(gpio_out_led_confirm, gpio.OUT)

def wait_for_confirmation():
    print('waiting for confirmation')
    def blink_confirm():
        gpio.add_event_detect(gpio_in_confirm, gpio.RISING, bouncetime=20)
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
    else:
        print('lampoverride detected')
    print('ran warninglamp')

def run_bell(time):
    print('run_bell %s.'%time)
    if gpio.input(gpio_in_belloverride):
        gpio.output(gpio_out_bell, True)
        sleep(time)
        gpio.output(gpio_out_bell, False)
    else:
        print('belloverride detected')
    print('ran bell')

def eval_doorbell(channel):
    print('Edge detected on channel %s, eval_doorbell.'%channel)
    #sleep(0.0003)
    debounce_runs = 0
    debounce_false_score = 0
    while debounce_runs < 10:
        if gpio.input(channel):
            debounce_false_score += 1
        debounce_runs += 1
    if debounce_false_score > 5:
        print('Signal on channel %s did not pass primitive debouncing.'%channel)
        return
    warninglampthread = threading.Thread(target=lambda: run_warninglamp(10, 0))
    bellthread = threading.Thread(target=lambda: run_bell(3))
    warninglampthread.start()
    bellthread.start()


def eval_phone():
    #TODO
    #while phone_ringing():
    #run_warninglamp(1)
    pass

setup_gpios()
gpio.add_event_detect(gpio_in_doorbell, gpio.FALLING, callback=eval_doorbell, bouncetime=1)
fritzlampthread=threading.Thread(target=lambda: fritzlamp.main())
fritzlampthread.start()
