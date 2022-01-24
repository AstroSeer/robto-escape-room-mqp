#  ___   ___  ___  _   _  ___   ___   ____ ___  ____  
# / _ \ /___)/ _ \| | | |/ _ \ / _ \ / ___) _ \|    \ 
#| |_| |___ | |_| | |_| | |_| | |_| ( (__| |_| | | | |
# \___/(___/ \___/ \__  |\___/ \___(_)____)___/|_|_|_|
#                  (____/ 
# Osoyoo Raspberry Pi Web Camera Control Robot Car
# tutorial url: https://osoyoo.com/?p=32066

from __future__ import division
import time
# import curses
#from pynput import keyboard
import Adafruit_PCA9685 # Import the PCA9685 module.
from flask import Flask, render_template, request
import RPi.GPIO as GPIO
import pyglet   #
import subprocess
from enum import Enum


pi_ip_address='130.215.9.186' # our Raspberry Pi IP address
pwm = Adafruit_PCA9685.PCA9685() # Initialise the PCA9685 using the default address (0x40).
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
move_speed = 1800  # Max pulse length out of 4096
turn_speed = 1500
cur_speed = turn_speed
# servo_lft = 500 #ultrasonic sensor facing right
servo_ctr = 320 #ultrasonic sensor facing front
# servo_rgt = 150 #ultrasonic sensor facing left

LRservo_cur = servo_ctr
UDservo_cur = servo_ctr
LRcam_servo = 15 #left/right camera servo
UDcam_servo = 14 #up/down camera servo

maxRight = 120
maxLeft = 550
maxUp = 190
maxDown = 424
step = 20


#initialize GPIO status variables
IN1Sts = 0
IN2Sts = 0
ENASts = 0
IN3Sts = 0
IN4Sts = 0
ENBSts = 0

        
def changespeed(speed):
    pwm.set_pwm(ENB, 0, speed)
    pwm.set_pwm(ENA, 0, speed)
#     pwm.set_pwm(ENA, 0, int(speed*.8))

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

def backward():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    changespeed(move_speed)
    
def forward():
    print("in forward")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    changespeed(move_speed)

def turnright():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    changespeed(turn_speed)
    
def turnleft():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    changespeed(turn_speed)

def center_car(direction, diff):
    global cur_speed
    Kp = 0.25
    if(direction):
#         print("turning right")
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
#         cur_speed = cur_speed - (Kp * abs(diff))
#         print("turn speed:",cur_speed)
#         changespeed(cur_speed)
    else:
#         print("turning left")
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
#         cur_speed = cur_speed - (Kp * abs(diff))
#         print("turn speed:",cur_speed)
#         changespeed(cur_speed)
    cur_speed = cur_speed - int(Kp * abs(diff))
    print("turn speed:",cur_speed)
    changespeed(cur_speed)
        
def turnright_pid(diff):
    Kp = 0.1
    print("turning right")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    changespeed(move_speed - (Kp * abs(diff)))
    print(move_speed - (Kp * abs(diff)))

    

def turnCam(camDir):
    global LRservo_cur, UDservo_cur
    print(camDir)
    if camDir == 1:
        LRservo_cur = LRservo_cur - step  #120
        print(LRservo_cur)
        if LRservo_cur <= maxRight:
            LRservo_cur = maxRight            
        pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
    elif camDir == 2:
        LRservo_cur = LRservo_cur + step #500
        print(LRservo_cur)
        if LRservo_cur >= maxLeft:
            LRservo_cur = maxLeft            
        pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
    elif camDir == 3:
        UDservo_cur = UDservo_cur - step #120
        print(UDservo_cur)
        if UDservo_cur <= maxUp:
            UDservo_cur = maxUp            
        pwm.set_pwm(UDcam_servo, 0, UDservo_cur)
    elif camDir == 4:
        UDservo_cur = UDservo_cur + step #500
        print(UDservo_cur)
        if UDservo_cur >= maxDown:
            UDservo_cur = maxDown            
        pwm.set_pwm(UDcam_servo, 0, UDservo_cur)
        

def centerCam():
    global LRservo_cur, UDservo_cur
    LRservo_cur = servo_ctr
    UDservo_cur = servo_ctr 
    pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
    pwm.set_pwm(UDcam_servo, 0, UDservo_cur)
    
def centerBase():
    global LRservo_cur
    Kp = 0.05
    diff = servo_ctr - LRservo_cur
    print(diff,(Kp*diff))
    slow_cam = 0
    while 5 < diff or diff < -5:
        print(slow_cam)
        if(diff > 0):
            direction = True
            if(slow_cam == 1):
                LRservo_cur = LRservo_cur + 2
                slow_cam = 0
        else:
            direction = False
            if(slow_cam == 1):
                LRservo_cur = LRservo_cur - 2
                slow_cam = 0
        center_car(direction, diff/7)
        #time.sleep(0.1)
        #LRservo_cur = LRservo_cur + int(Kp * diff)
        print("servo position",LRservo_cur)
        pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
        diff = servo_ctr - LRservo_cur
        slow_cam = slow_cam+1
    stopcar()
        
#initialize robot
stopcar()
pwm.set_pwm(LRcam_servo, 0, servo_ctr)
pwm.set_pwm(UDcam_servo, 0, servo_ctr)
time.sleep(2)

running = True

forwards = 0
backwards = 0
left = 0
right = 0

camleft = 0
camright = 0
camup = 0
camdown = 0
camcenter = 0
try:
    while running:
#         turnright_pid(100)
#         time.sleep(.5)
#         stopcar()
        LRservo_cur = maxLeft
        pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
        time.sleep(2)
        centerBase()
        print(LRservo_cur, servo_ctr)
        running = False


finally:
    print("ending")
    pwm.set_pwm(LRcam_servo, 0, servo_ctr)
    pwm.set_pwm(UDcam_servo, 0, servo_ctr)
#     curses.nocbreak()
#     key.keypad(0)
#     curses.echo()
#     curses.endwin()
    GPIO.cleanup()
