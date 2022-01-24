import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM) # GPIO number  in BCM mode
GPIO.setwarnings(False)

LEDpin = 26
UVpin = 6

GPIO.setup(LEDpin, GPIO.OUT)
GPIO.setup(UVpin, GPIO.OUT)

i = 0

while(i < 3):
    GPIO.output(LEDpin,GPIO.HIGH)
    GPIO.output(UVpin,GPIO.LOW)
    time.sleep(1)
    GPIO.output(LEDpin,GPIO.LOW)
    GPIO.output(UVpin,GPIO.HIGH)
    time.sleep(1)
    i = i + 1

GPIO.output(LEDpin,GPIO.LOW)
GPIO.output(UVpin,GPIO.LOW)
GPIO.cleanup()
