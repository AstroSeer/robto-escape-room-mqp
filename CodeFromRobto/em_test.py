import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM) # GPIO number  in BCM mode
GPIO.setwarnings(False)

EMpin = 16

GPIO.setup(EMpin, GPIO.OUT)

i = 0

while(i < 2):
    GPIO.output(EMpin,GPIO.HIGH)
    time.sleep(1)
    GPIO.output(EMpin,GPIO.LOW)
    time.sleep(1)
    i = i + 1

GPIO.output(EMpin,GPIO.LOW)
GPIO.cleanup()