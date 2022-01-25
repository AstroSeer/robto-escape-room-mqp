#  ___   ___  ___  _   _  ___   ___   ____ ___  ____  
# / _ \ /___)/ _ \| | | |/ _ \ / _ \ / ___) _ \|    \ 
#| |_| |___ | |_| | |_| | |_| | |_| ( (__| |_| | | | |
# \___/(___/ \___/ \__  |\___/ \___(_)____)___/|_|_|_|
#                  (____/ 
# Osoyoo Raspberry Pi Web Camera Control Robot Car
# tutorial url: https://osoyoo.com/?p=32066

from __future__ import division
import time
# Import the PCA9685 module.
import Adafruit_PCA9685
from flask import Flask, render_template, request
import RPi.GPIO as GPIO
pi_ip_address='130.215.210.19' # replace 192.168.0.107 with your Raspberry Pi IP address
# Initialise the PCA9685 using the default address (0x40).
pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(60)


app = Flask(__name__)
GPIO.setmode(GPIO.BCM) # GPIO number  in BCM mode
GPIO.setwarnings(False)
#define actuators GPIOs
IN1 = 23
IN2 = 24
IN3 = 27
IN4 = 22
ENA = 0  #Right motor speed PCA9685 port 0
ENB = 1  #Left motor speed PCA9685 port 1
move_speed = 2000  # Max pulse length out of 4096
servo_lft = 500 #ultrasonic sensor facing right
servo_ctr = 300 #ultrasonic sensor facing front
servo_rgt = 150 #ultrasonic sensor facing left

#initialize GPIO status variables
IN1Sts = 0
IN2Sts = 0
ENASts = 0
IN3Sts = 0
IN4Sts = 0
ENBSts = 0

def changespeed(speed):
    pwm.set_pwm(ENA, 0, speed)
    pwm.set_pwm(ENB, 0, speed)

# Define motor control  pins as output
GPIO.setup(IN1, GPIO.OUT)   
GPIO.setup(IN2, GPIO.OUT) 
GPIO.setup(IN3, GPIO.OUT)   
GPIO.setup(IN4, GPIO.OUT) 

def stopcar():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    changespeed(0)  
stopcar()

def backward():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    changespeed(move_speed)
    #following two lines can be removed if you want car make continuous movement without pause
    #time.sleep(0.25)  
    #stopcar()
    
def forward():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    changespeed(move_speed)
    #following two lines can be removed if you want car make continuous movement without pause
    #time.sleep(0.25)  
    #stopcar()
    
def turnright():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    changespeed(move_speed)
    #following two lines can be removed if you want car make continuous movement without pause
    #time.sleep(0.25)  
    #stopcar()
    
def turnleft():
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    changespeed(move_speed)
    #following two lines can be removed if you want car make continuous movement without pause
    #time.sleep(0.25)  
    #stopcar()
pwm.set_pwm(15, 0, servo_ctr)
time.sleep(2)

@app.route("/")
def hello():
   return render_template('index.html')
   
@app.route("/<action>/<cmd>")
def action(action,cmd):
    if action=='camera':
        degree= 505-int(cmd)*2
        pwm.set_pwm(15, 0, degree)
        print(degree)
             
    if action=='move':
        if cmd=='forward':
            forward()
        if cmd=='backward':
            backward()
        if cmd=='turnleft':
            turnleft()
        if cmd=='turnright':
            turnright()
        if cmd=='stopcar':
            stopcar()
    if action=='speed':
        if cmd=='high':
            changespeed(75)
            print("speed changed to 75")
        if cmd=='regular':
            changespeed(50)
            print("speed changed to 50")
        if cmd=='low':
            changespeed(25)
            print("speed changed to 25")
        if cmd=='zero':
            changespeed(0)
            print("speed changed to 0")
            

    return render_template('index.html')
if __name__ == "__main__":
   app.run(host=pi_ip_address, port=80, debug=True)

