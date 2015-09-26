import RPi.GPIO as gpio
import subprocess
from time import sleep

gpio_in_doorbell = 11
gpio_in_lampoverride = 12
gpio_in_hornoverride = 13
gpio_in_printoverride = 14
gpio_in_confirm = 17

gpio_out_warninglamp = 15
gpio_out_horn = 20
gpio_out_led_doorbell = 18
gpio_out_led_confirm = 19

def setup_gpios():
    gpio.setup(gpio_in_doorbell, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    gpio.setup(gpio_in_lampoverride, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    gpio.setup(gpio_in_hornoverride, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    gpio.setup(gpio_in_printoverride, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    gpio.setup(gpio_in_confirm, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    gpio.setup(gpio_out_warninglamp, GPIO.OUT)
    gpio.setup(gpio_out_horn, GPIO.OUT)
    gpio.setup(gpio_out_led_doorbell, GPIO.OUT)
    gpio.setup(gpio_out_led_confirm, GPIO.OUT)

def wait_for_confirmation():
    def blink_confirm():
        gpio.add_event_detect(gpio_in_confirm, gpio.RISING, bouncetime=200)
        while not gpio.event_detected(gpio_in_confirm):
            gpio.output(gpio_out_led_confirm, TRUE)
            sleep(500)
            gpio.output(gpio_out_led_confirm, FALSE)
            sleep(500)
        gpio.remove_event_detect(gpio_in_confirm)
    subprocess.Popen(blink_confirm())
    gpio.wait_for_edge(gpio_in_confirm, gpio.RISING)


def run_warninglamp(time, confirm):
    if gpio.input(gpio_in_lampoverride):
        gpio.output(gpio_out_warninglamp, TRUE)
        sleep(time)
        if confirm:
            wait_for_confirmation()
        gpio.output(gpio_out_warninglamp, FALSE)

def sound_horn(pattern, time):
    #TODO
    pass

def eval_doorbell(channel):
    print('Edge detected on channel %s, eval_doorbell.'%channel)
    gpio.output(gpio_out_led_doorbell, TRUE)
    subprocess.Popen(run_warninglamp(10, 0))
    gpio.wait_for_edge(gpio_in_doorbell, gpio.RISING)
    gpio.output(gpio_out_led_doorbell, FALSE)


def eval_phone():
    #TODO
    #while phone_ringing():
    #run_warninglamp(1)
    pass


gpio.add_event_detect(gpio_in_doorbell, gpio.FALLING, callback=eval_doorbell, bouncetime=200)
