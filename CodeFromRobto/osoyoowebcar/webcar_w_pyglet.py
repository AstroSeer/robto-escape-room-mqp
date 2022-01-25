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
# import pygame


class CamDirection(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

pi_ip_address='130.215.210.19' # our Raspberry Pi IP address
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


# pygame.init()
# pygame.event.set_grab(True)
# pygame.key.start_text_input()
# pygame.display.set_mode(pygame.HIDDEN)

key = pyglet.window.key
window = pyglet.window.Window()

label = pyglet.text.Label('Hello, world',
                          font_name='Times New Roman',
                          font_size=36,
                          x=window.width//2, y=window.height//2,
                          anchor_x='center', anchor_y='center')

@window.event
def on_draw():
    window.clear()
    label.draw()
    #window.activate()

@window.event
def on_key_press(symbol, modifiers):
    global forwards, backwards, right, left, camright, camleft, camup, camdown, camcenter, label
    try:            
        if symbol == key.W:
            forwards = 1
        elif symbol == key.A:
            left = 1
        elif symbol == key.S:
            backwards = 1
        elif symbol == key.D:
            right = 1
        elif symbol == key.RIGHT: #turn servo right
            camright = 1
        elif symbol == key.LEFT:#turn servo left
            camleft = 1
        elif symbol == key.UP:    #center camera
            camup = 1
        elif symbol == key.DOWN:
            camdown = 1
        elif symbol == key.ENTER:
            camcenter = 1

    except AttributeError:
       print('')
        
@window.event
def on_key_release(symbol, modifiers):
    global forwards, backwards, right, left, running, camright, camleft, camup,camdown, camcenter
    try:
        if symbol == key.ESCAPE:
            running = False
            return False
        elif symbol == key.W:
            forwards = 0
        elif symbol == key.A:
            left = 0
        elif symbol == key.S:
            backwards = 0
        elif symbol == key.D:
            right = 0
        elif symbol == key.RIGHT: #turn servo right
            camright = 0
        elif symbol == key.LEFT:#turn servo left
           camleft = 0
        elif symbol == key.UP: #center camera
            camup = 0
        elif symbol == key.DOWN:
            camdown = 0
        elif symbol == key.ENTER:
            camcenter = 0
        
    except AttributeError:
        print('')
        
def changespeed(speed):
    pwm.set_pwm(ENB, 0, speed)
    pwm.set_pwm(ENA, 0, int(speed*.8))

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

def update(dt):
        if forwards == 1:
            forward()
            print("forward\n")
        elif backwards == 1:
            backward()
            print("backward\n")
        elif right == 1:
            turnright()
            print("turn right\n")
        elif left == 1:
            turnleft()
            print("turn left\n")
        else:
            stopcar()
            
        if camcenter == 1:
            centerCam()
        elif camright == 1:
#             print(repr(CamDirection.RIGHT))
            turnCam(CamDirection.RIGHT.value)
        elif camleft == 1:
#             print(repr(CamDirection.LEFT))
            turnCam(CamDirection.LEFT.value)
        elif camup == 1:
#             print(repr(CamDirection.UP))
            turnCam(CamDirection.UP.value)
        elif camdown == 1:
#             print(repr(CamDirection.DOWN))
            turnCam(CamDirection.DOWN.value)
            
def repUpdate():
    i = 29
    while(running):
        i = i+1
        if i==30:
            i = 0
            update(.01)
try:              
    pyglet.clock.schedule_interval(update, 0.01)
    pyglet.app.run()
#     while(running):
#         print()
#         for event in pygame.event.get():
#             print("key event")
#             repUpdate()
#             if event.type == pygame.KEYDOWN:
#                 on_key_press(event.key.get_pressed())
#             if event.type == pygame.KEYUP:
#                 on_key_release(event.key)

finally:
    print("ending")
    pwm.set_pwm(LRcam_servo, 0, servo_ctr)
    pwm.set_pwm(UDcam_servo, 0, servo_ctr)
#     curses.nocbreak()
#     key.keypad(0)
#     curses.echo()
#     curses.endwin()
    GPIO.cleanup()