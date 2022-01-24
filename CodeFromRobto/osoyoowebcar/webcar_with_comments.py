#  ___   ___  ___  _   _  ___   ___   ____ ___  ____  
# / _ \ /___)/ _ \| | | |/ _ \ / _ \ / ___) _ \|    \ 
#| |_| |___ | |_| | |_| | |_| | |_| ( (__| |_| | | | |
# \___/(___/ \___/ \__  |\___/ \___(_)____)___/|_|_|_|
#                  (____/ 
# Osoyoo Raspberry Pi Web Camera Control Robot Car
# tutorial url: https://osoyoo.com/?p=32066

from __future__ import division
import time
import curses
#from pynput import keyboard
import Adafruit_PCA9685 # Import the PCA9685 module.
from flask import Flask, render_template, request
import RPi.GPIO as GPIO
import pyglet
import subprocess



pi_ip_address='130.215.209.212' # replace 192.168.0.107 with your Raspberry Pi IP address
pwm = Adafruit_PCA9685.PCA9685() # Initialise the PCA9685 using the default address (0x40).
pwm.set_pwm_freq(60)
 
screen = curses.initscr()   #initialize curses
curses.noecho()
curses.halfdelay(5)
curses.cbreak()
screen.keypad(True)

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
servo_lft = 500 #ultrasonic sensor facing right
servo_ctr = 300 #ultrasonic sensor facing front
servo_rgt = 150 #ultrasonic sensor facing left
servo_cur = servo_ctr
LRcam_servo = 15 #left/right camera servo
UDcam_servo = 14 #up/down camera servo 

#initialize GPIO status variables
IN1Sts = 0
IN2Sts = 0
ENASts = 0
IN3Sts = 0
IN4Sts = 0
ENBSts = 0

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
    global forwards, backwards, right, left, camright, camleft, camcenter, label
    print("lkjas;ldf")
    try:
#         print(";ljkjsda")
#         label = pyglet.text.Label("blarg",
#                           font_name='Times New Roman',
#                           font_size=36,
#                           x=window.width//2, y=window.height//2,
#                           anchor_x='center', anchor_y='center')
        
        
#         print('alphanumeric key {0} pressed'.format(
#             key.char))
        #ch = key.char
        
#         if ch == 'w':
#             forwards = 1
#             #forward()
#         elif ch == 'a':
#             left = 1
#             #turnleft()
#         elif ch == 's':
#             backwards = 1
#             #backward()
#         elif ch == 'd':
#             right = 1
            
        if symbol == key.W:
            forwards = 1
            #forward()
        elif symbol == key.A:
            left = 1
            #turnleft()
        elif symbol == key.S:
            backwards = 1
            #backward()
        elif symbol == key.D:
            right = 1
            print("right!")
        elif symbol == key.RIGHT: #turn servo right
            camright = 1
        elif symbol == key.LEFT:#turn servo left
            camleft = 1
        elif symbol == key.UP:    #center camera
            camcenter = 1
            #print(right)
            #print("right!!!")
            #turnright()
        #else:
            #stopcar()
#             #print("shitty else")
            
            
        
    except AttributeError:
       print('')
#         print('special key {0} pressed'.format(
#             key))
        
#         if key == keyboard.Key.right: #turn servo right
#             camright = 1
#         elif key == keyboard.Key.left:#turn servo left
#            camleft = 1
#         elif key == keyboard.Key.up:    #center camera
#             camcenter = 1
        
@window.event
def on_key_release(symbol, modifiers):
    global forwards, backwards, right, left, running, camright, camleft, camcenter
    try:
#         print('alphanumeric key {0} released'.format(
#             key.char))
        #ch = key.char
        if symbol == key.ESCAPE:
            running = False
            return False
        elif symbol == key.W:
            forwards = 0
            #forward()
        elif symbol == key.A:
            left = 0
            #turnleft()
        elif symbol == key.S:
            backwards = 0
            #backward()
        elif symbol == key.D:
            right = 0
            #print("released d")
        elif symbol == key.RIGHT: #turn servo right
            camright = 0
            print("right released")
        elif symbol == key.LEFT:#turn servo left
           camleft = 0
        elif symbol == key.UP:    #center camera
            camcenter = 0
            
            #turnright()
        #else:
            #stopcar()
#             print("shitty else")
            
            
        
    except AttributeError:
        print('')
#         print('special key {0} released'.format(
#             key))
#         if key == keyboard.Key.esc:
#             # Stop listener
#             running = False
#             return False
#         elif key == keyboard.Key.right: #turn servo right
#             camright = 0
#         elif key == keyboard.Key.left:#turn servo left
#            camleft = 0
#         elif key == keyboard.Key.up:    #center camera
#             camcenter = 0
        
        
        
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
    #following two lines can be removed if you want car make continuous movement without pause
    #time.sleep(0.3)  
    #stopcar()
    
def forward():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    changespeed(move_speed)
    #following two lines can be removed if you want car make continuous movement without pause
    #time.sleep(0.3)  
    #stopcar()
    
def turnright():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    changespeed(turn_speed)
    #following two lines can be removed if you want car make continuous movement without pause
    #time.sleep(0.3)  
    #stopcar()
    
def turnleft():
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    changespeed(turn_speed)
    #following two lines can be removed if you want car make continuous movement without pause
    #time.sleep(0.3)  
    #stopcar()
    
def turnCam(turnRight):
    global servo_cur
    if turnRight:
        servo_cur = servo_cur - 8  #120
        if servo_cur <= 120:
            servo_cur = 120            
        pwm.set_pwm(LRcam_servo, 0, servo_cur)
    else:
        servo_cur = servo_cur + 8 #500
        if servo_cur >= 500:
            servo_cur = 500            
        pwm.set_pwm(LRcam_servo, 0, servo_cur)
        #print(servo_cur)
        


def centerCam():
    global servo_cur
    servo_cur = servo_ctr
    pwm.set_pwm(LRcam_servo, 0, servo_cur)
    
#initialize robot
stopcar()
pwm.set_pwm(LRcam_servo, 0, servo_ctr)
time.sleep(2)

running = True


forwards = 0
backwards = 0
left = 0
right = 0


camleft = 0
camright = 0
camcenter = 0

# ...or, in a non-blocking fashion:
# listener = keyboard.Listener(
#     on_press=on_press,
#     on_release=on_release)
# try:
#     listener.start()
# except MyException as e:
#         print('{0} was pressed'.format(e.args[0]))


# @app.route("/")
# def hello():
#    return render_template('index.html')
#    
# @app.route("/<action>/<cmd>")
# def action(action,cmd):
#     if action=='camera':
#         degree= 505-int(cmd)*2
#         pwm.set_pwm(15, 0, degree)
#         print(degree)
#              
#     if action=='move':
#         if cmd=='forward':
#             forward()
#         if cmd=='backward':
#             backward()
#         if cmd=='turnleft':
#             turnleft()
#         if cmd=='turnright':
#             turnright()
#         if cmd=='stopcar':
#             stopcar()
#     if action=='speed':
#         if cmd=='high':
#             changespeed(75)
#             print("speed changed to 75")
#         if cmd=='regular':
#             changespeed(50)
#             print("speed changed to 50")
#         if cmd=='low':
#             changespeed(25)
#             print("speed changed to 25")
#         if cmd=='zero':
#             changespeed(0)
#             print("speed changed to 0")
#             
# 
#     return render_template('index.html')
# if __name__ == "__main__":
#    app.run(host=pi_ip_address, port=80, debug=True)

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
            #check if right AND forward, move right and forward?
        elif left == 1:
            turnleft()
            print("turn left\n")
        else:
            stopcar()
            
        if camcenter == 1:
            centerCam()
        elif camright == 1:
            turnCam(True)
        elif camleft == 1:
            turnCam(False)
            
def repUpdate():
    i = 29
    while(running):
        i = i+1
        if i==30:
            i = 0
            update(.01)
try:
        
#         i = 29
#         while running:
#             label = pyglet.text.Label(i,
#                           font_name='Times New Roman',
#                           font_size=36,
#                           x=window.width//2, y=window.height//2,
#                           anchor_x='center', anchor_y='center')
#             i = i + 1
#             if i==30:
#                 i = 0
        
                    
                    
        pyglet.clock.schedule_interval(update, 0.01)
        #p = subprocess.run(
        pyglet.app.run()#)
        #p2 = subprocess.run(repUpdate())
        #print("lllllllallllalll")
        
            
                    
                    #print("stop car\n")
#             
#             while screen.getch() is not -1:
#                 curses.flushinp()
#                 char = screen.getch()
#                 print(char)
#                 if char == ord('w'):
#                     forward()
#                 elif char == ord('a'):
#                     turnleft()
#                 elif char == ord('s'):
#                     backward()
#                 elif char == ord('d'):
#                     turnright()
#                 elif char == curses.KEY_RIGHT: #turn servo right
#                     if servo_cur <= 120:
#                         servo_cur = 120
#                     else:
#                         servo_cur = servo_cur - 10  #120
#                     pwm.set_pwm(15, 0, servo_cur)
#                     #print(servo_cur)
#                 elif char == curses.KEY_LEFT:#turn servo left
#                     if servo_cur >= 500:
#                         servo_cur = 500
#                     else:
#                         servo_cur = servo_cur + 10 #500
#                     pwm.set_pwm(15, 0, servo_cur)
#                     #print(servo_cur)
#                 elif char == curses.KEY_UP:    #center camera
#                     servo_cur = servo_ctr
#                     pwm.set_pwm(15, 0, servo_cur)
#                 else:
#                     stopcar()
#                     print("shitty else")
#             #else:        
#             stopcar()
#             print("shitty else")
finally:
    print("ending")
    #Close down curses properly, inc turn echo back on!
    curses.nocbreak(); screen.keypad(0); curses.echo()
    curses.endwin()
    GPIO.cleanup()