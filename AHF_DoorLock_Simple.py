import RPi.GPIO as GPIO
import time
from time import sleep

# New part for enabling door lock
servoPIN = 17
GPIO.setmode(GPIO.BOARD)  # naming all the pins
GPIO.setup(servoPIN, GPIO.OUT)  # PWM signal set on output in 17

p = GPIO.PWM(servoPIN, 50)  # GPIO 17 for PWM with 50Hz
p.start(0)  # Initialization


def setAngle(angle):
    duty = angle / 18 + 2
    GPIO.output(servoPIN, True)
    p.ChangeDutyCycle(duty)
    time.sleep(1)
    GPIO.output(servoPIN, False)
    p.ChangeDutyCycle(0)
