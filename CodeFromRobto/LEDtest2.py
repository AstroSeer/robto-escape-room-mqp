import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM) # GPIO number  in BCM mode
GPIO.setwarnings(False)

LEDpin = 16

GPIO.setup(LEDpin, GPIO.OUT)


while(1):
    GPIO.output(LEDpin, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(LEDpin, GPIO.LOW)
    time.sleep(1)
    
GPIO.cleanup()