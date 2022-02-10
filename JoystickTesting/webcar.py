#  ___   ___  ___  _   _  ___   ___   ____ ___  ____  
# / _ \ /___)/ _ \| | | |/ _ \ / _ \ / ___) _ \|    \ 
#| |_| |___ | |_| | |_| | |_| | |_| ( (__| |_| | | | |
# \___/(___/ \___/ \__  |\___/ \___(_)____)___/|_|_|_|
#                  (____/ 
# Osoyoo Raspberry Pi Web Camera Control Robot Car
# tutorial url: https://osoyoo.com/?p=32066

from __future__ import division
import time
import flask
from flask import Response
import threading
import atexit
import RobtoCam#Test
import Adafruit_PCA9685 #--- add back in
from flask import Flask, render_template, request, send_from_directory
import RPi.GPIO as GPIO #--- add back in
from enum import Enum


pi_ip_address='130.215.15.174'#'localhost'

# Initialise the PCA9685 using the default address (0x40).
pwm = Adafruit_PCA9685.PCA9685() #--- add back in
pwm.set_pwm_freq(60)#--- add back in


import os     #importing os library so as to communicate with the system
os.system ("sudo pigpiod") #Launching GPIO library
time.sleep(1) # As i said it is too impatient and so if this delay is removed you will get an error
import pigpio #importing GPIO library

#TODO
#make it so that if it has not recieved anything from the html for a while, 
    #it stops moving

   
   
   


class CamDirection(Enum):
    NONE = 0
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4


class CarDirection(Enum):
    NONE = 0
    FORWARD = 1
    FOR_RIGHT = 2
    TURN_RIGHT = 3
    BACK_RIGHT = 4
    BACK = 5
    BACK_LEFT = 6
    TURN_LEFT = 7
    FOR_LEFT = 8
    
class Button(Enum):
    OFF = 0
    ON = 1

cam = RobtoCam.Camera()
#with this variable cam, can access the object's properties
    #in order to get the information from the vision processing code



#app = Flask(__name__) #keep commented


GPIO.setmode(GPIO.BCM) # GPIO number  in BCM mode #--- add back in
GPIO.setwarnings(False) #--- add back in

#define actuators GPIOs 
IN1 = 23 #--- add back in
IN2 = 24 #--- add back in
IN3 = 27 #--- add back in
IN4 = 22 #--- add back in
ENA = 0  #Right motor speed PCA9685 port 0 #--- add back in
ENB = 1  #Left motor speed PCA9685 port 1 #--- add back in
move_speed = 1800  # Max pulse length out of 4096 #--- add back in
turn_speed = 1500 #--- add back in

servo_ctr = 320 #ultrasonic sensor facing front

# servo_rgt = 150 #ultrasonic sensor facing left #unneeded?? ask owen
# servo_lft = 500 #ultrasonic sensor facing right #unneeded?? ask owen


LRservo_cur = servo_ctr
UDservo_cur = servo_ctr
LRcam_servo = 15 #left/right camera servo
UDcam_servo = 14 #up/down camera servo

maxRight = 120
maxLeft = 550
maxUp = 190
maxDown = 424
step = 3#20 #how far camera servos move in one step

#initialize GPIO status variables
IN1Sts = 0 #--- add back in
IN2Sts = 0 #--- add back in
ENASts = 0 #--- add back in
IN3Sts = 0 #--- add back in
IN4Sts = 0 #--- add back in
ENBSts = 0 #--- add back in


# Define motor control  pins as output
GPIO.setup(IN1, GPIO.OUT)    #--- add back in
GPIO.setup(IN2, GPIO.OUT)  #--- add back in
GPIO.setup(IN3, GPIO.OUT)    #--- add back in
GPIO.setup(IN4, GPIO.OUT)  #--- add back in
        
# Define peripheral pins
lightPin = 25
UVPin = 3
whitePin = 2
magnetPin = 4
GPIO.setup(lightPin, GPIO.IN)
# For Lift
ESC=13  #Connect the ESC in this GPIO pin 
speed = 200
stop = 1500

pi = pigpio.pi();
time.sleep(1)
pi.set_servo_pulsewidth(ESC, stop)
        
        
def changespeed(speed):
    #print("changeSpeed") #--- only for testing
    pwm.set_pwm(ENB, 0, speed) #--- add back in
    pwm.set_pwm(ENA, 0, int(speed*.95)) #--- add back in





def stopcar():
    #print("stopping car")
    #return #--- only for testing
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    changespeed(0)  

def backward():
    #print("going back")
    #return #--- only for testing
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    changespeed(move_speed)
    
def forward():
    #print("going forward")
    #return #--- only for testing
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    changespeed(move_speed)

def turnright():
    #print("turning right")
    #return #--- only for testing
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    changespeed(turn_speed)
    
def turnleft():
    #print("turning left")
    #return #--- only for testing
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    changespeed(turn_speed)
    
def turnCam():#camDir):
    #print("turning cam: " + str(camDir))
    #return #--- only for testing
    global LRservo_cur, UDservo_cur
    
    if camDirX == CamDirection.RIGHT.value:
        LRservo_cur = LRservo_cur - step  #120
        print(LRservo_cur)
        if LRservo_cur <= maxRight:
            LRservo_cur = maxRight            
        pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
    elif camDirX == CamDirection.LEFT.value:
        LRservo_cur = LRservo_cur + step #500
        print(LRservo_cur)
        if LRservo_cur >= maxLeft:
            LRservo_cur = maxLeft            
        pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
    
    if camDirY == CamDirection.UP.value:
        UDservo_cur = UDservo_cur - step #120
        print(UDservo_cur)
        if UDservo_cur <= maxUp:
            UDservo_cur = maxUp            
        pwm.set_pwm(UDcam_servo, 0, UDservo_cur)
    elif camDirY == CamDirection.DOWN.value:
        UDservo_cur = UDservo_cur + step #500
        print(UDservo_cur)
        if UDservo_cur >= maxDown:
            UDservo_cur = maxDown            
        pwm.set_pwm(UDcam_servo, 0, UDservo_cur)
    
        

def centerCam():
    print("centering cam")
    #return #--- only for testing
    global LRservo_cur, UDservo_cur
    LRservo_cur = servo_ctr
    UDservo_cur = servo_ctr 
    pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
    pwm.set_pwm(UDcam_servo, 0, UDservo_cur)
    
#initialize robot
stopcar()
pwm.set_pwm(LRcam_servo, 0, servo_ctr)#--- add back in
pwm.set_pwm(UDcam_servo, 0, servo_ctr)#--- add back in
time.sleep(2)

running = True

carDir = CarDirection.NONE.value

camDirX = CamDirection.NONE.value
camDirY = CamDirection.NONE.value
cam_center = False
buttonVals = [0,0,0,0,0,0,0,0,0]
prevButtons = [0,0,0,0,0,0,0,0,0]
prevButtonState = [0,0,0,0,0,0,0,0,0]
hasBlock = False


def update(dt):
        #if python 3.10 or above, can use "match", works like switch statements 
        if carDir == CarDirection.NONE.value:
            stopcar()
        elif carDir == CarDirection.FORWARD.value:
            forward()
            #print("forward")
        elif carDir == CarDirection.BACK.value:
            backward()
            #print("backward")
        elif carDir == CarDirection.TURN_RIGHT.value:
            turnright()
           # print("turn right")
        elif carDir == CarDirection.TURN_LEFT.value:
            turnleft()
            #print("turn left")
            
        #code for implementing diagonal values for movement joystick
        # elif carDir == CarDirection.FOR_LEFT.value:
            # #print("front left")
        # elif carDir == CarDirection.FOR_RIGHT.value:
            # #print("front right")
        # elif carDir == CarDirection.BACK_LEFT.value:
            # #print("back right")
        # elif carDir == CarDirection.BACK_RIGHT.value:
            #print("back right")
        #else:
            #print("carDir: " + str(carDir))
            #stopcar()
            
        if cam_center:
            centerCam()
        else:
            turnCam()
            
app = Flask(__name__, static_url_path='')


@app.route("/")
def hello():
   return render_template('testing.html')


@app.route("/data")
def recieve1():#buttonvals,moveAxesVal,camAxesVals):
    global carDir, camDirX, camDirY, buttonVals, prevButtonState, prevButtons
    print("received")
    tempCar = int(request.args.get('car'))
    if(tempCar>=0 and tempCar <=8):#TODO check if valid
        carDir = tempCar
    #print(carDir)
    tempCams = request.args.get('cam')
    tempCamsX = int(tempCams[0])
    tempCamsY = int(tempCams[1])
    if(True): #TODO check if valid
        camDirX = tempCamsX
        camDirY = tempCamsY
    #print("X: " + str(tempCamsX) + ", Y: " + str(tempCamsY))
    tempButtons = request.args.get('buttons')
    if(len(tempButtons) == 9):
        for i in range(9):
            butVal = int(tempButtons[i])
            if(butVal == 0 or butVal == 1):
                buttonVals[i] = butVal

    print(buttonVals)
    print(prevButtons)
    print(prevButtonState)
    
    # Checks UV Flashlight
    if(buttonVals[3]==0 and prevButtons[3]==1):
        if(prevButtonState[3]==0):
            prevButtonState[3] = uvFlashlight(1)
            print("turn on")
        elif(prevButtonState[3]==1):
            prevButtonState[3] = uvFlashlight(0)
            print("turn off")
    elif((buttonVals[3]==0 and prevButtons[3]==0) and buttonVals[4]==1):
        prevButtonState[3] = 0
    
    # Checks White Flashlight
    if(buttonVals[4]==0 and prevButtons[4]==1):
        if(prevButtonState[4]==0):
            prevButtonState[4] = whiteFlashlight(1)
            print("turn on")
        elif(prevButtonState[4]==1):
            prevButtonState[4] = whiteFlashlight(0)
            print("turn off")
    elif((buttonVals[4]==0 and prevButtons[4]==0) and buttonVals[3]==1):
        prevButtonState[4] = 0
        
    # Centers Camera
    if(buttonVals[5]==0 and prevButtons[5]==1):
        centerCam()
    
    # Checks Electromagnet
    if(buttonVals[6]==0 and prevButtons[6]==1):
        if(prevButtonState[6]==0):
            prevButtonState[6] = magnet(1)
            print("turn on")
        elif(prevButtonState[6]==1):
            prevButtonState[6] = magnet(0)
            print("turn off")
    
    # Moves lift up
    if(buttonVals[7]==0 and prevButtons[7]==1):
        if(prevButtonState[7]==0):
            prevButtonState[8] = 0
            prevButtonState[7] = liftUp(1)
            print("going up")
        else: print("already up")   
    
    # Moves lift down
    if(buttonVals[8]==0 and prevButtons[8]==1):
        if(prevButtonState[8]==0):
            prevButtonState[7] = 0
            prevButtonState[8] = liftDown(1)
            print("going down")
        else: print("already down")
        
    #Copies previous buttons
    for i in range(9):
        prevButtons[i] = buttonVals[i]
    
    return render_template('testing.html')
    
@app.route("/<buttonvals>/<moveAxesVal>/<camAxesVals>")
def recieve(buttonvals,moveAxesVal,camAxesVals):
   
    return render_template('testing.html')


#buttonvals will be 9 digits, either 0 or 1, in button order. 
    #nothing in between. eg "010101010"
    #can do a for loop, 0-9, take the value at each index of the string, 
    #then interpret each as an int and compare against current button values
    
#moveAxesVal is an int between 0-8, 
    #matches CarDirection enum

#camAxesVals is 2 ints, not separated by spaces,
    #first is x axis, either 0, 1, or 2.
    #second is y axis, either 0, 3, or 4.
    #matches CamDirection enum
    
# --- PERIPHERAL FUNCTIONS ---
def whiteFlashlight(status):
    if(status):
        pwm.set_pwm(whitePin, 0, 4000)
#         time.sleep(5)
    else:
        pwm.set_pwm(whitePin, 0, 0)
    pwm.set_pwm(UVPin, 0, 0)
    pwm.set_pwm(magnetPin, 0, 0)
    return status
    
def uvFlashlight(status):
    if(status):
        pwm.set_pwm(UVPin, 0, 4000)    #switch leds on and off
    else:
        pwm.set_pwm(UVPin, 0, 0)
    pwm.set_pwm(whitePin, 0, 0)
    pwm.set_pwm(magnetPin, 0, 0)
    return status

def magnet(status):
    if(status):
        pwm.set_pwm(magnetPin, 0, 4000)    #switch EM on and off
    else:
        pwm.set_pwm(magnetPin, 0, 0)
    pwm.set_pwm(whitePin, 0, 0)
    pwm.set_pwm(UVPin, 0, 0)
    return status

def liftUp(status):
    global hasBlock
    if(hasBlock):
        pi.set_servo_pulsewidth(ESC, stop-speed)
        time.sleep(2.5)
           
        pi.set_servo_pulsewidth(ESC, stop)
        time.sleep(1)
    else:
        pi.set_servo_pulsewidth(ESC, stop-speed)
        time.sleep(1.75)
           
        pi.set_servo_pulsewidth(ESC, stop)
        time.sleep(1) 
    return status

def liftDown(status):
    if(status):
        pi.set_servo_pulsewidth(ESC, stop+speed)
        time.sleep(1.75)
    
        pi.set_servo_pulsewidth(ESC, stop)
        time.sleep(1)
    return status


#TODO: fix problem when right click image and "open image in new tab"
@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(cam.start(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        
    
class MyThread(threading.Thread):
    def __init__(self, event):
        global count
        threading.Thread.__init__(self)
        self.stopped = event


    def run(self):
        old_time = time.time()
        while not self.stopped.wait(.01):
            dt = time.time()-old_time
            update(dt)
            old_time = time.time()
            


# def closeThreads():
    # global stopFlag
    # print("closing time")
    # stopFlag.set()
    
if __name__ == "__main__":
    try:
        stopFlag = threading.Event()
        thread = MyThread(stopFlag)
        thread.daemon=True
        thread.start()
        print("starting")
        #atexit.register(cleanup)
        app.run(host=pi_ip_address, port=8000, debug=False)#set debug off??
    finally:
        cleanup()
 
def cleanup():
    print("ending")
    pwm.set_pwm(LRcam_servo, 0, servo_ctr)
    pwm.set_pwm(UDcam_servo, 0, servo_ctr)
    GPIO.cleanup()

#In the code that started the timer, you can then set the stopped event to stop the timer.

# stopFlag = Event()
# thread = MyThread(stopFlag)
# thread.start()
# # this will stop the timer
# stopFlag.set()
   
#def repUpdate():
 #   i = 29
  #  while(running):
   #     i = i+1
    #    if i==30:
     #       i = 0
      #      update(.01)
#try:              
 #       pyglet.clock.schedule_interval(update, 0.01)
  #      pyglet.app.run()

#finally:
    #print("ending")
   # pwm.set_pwm(LRcam_servo, 0, servo_ctr)
    #pwm.set_pwm(UDcam_servo, 0, servo_ctr)
    #GPIO.cleanup()
