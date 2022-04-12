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
import RobtoCam
import Adafruit_PCA9685 #--- add back in
from flask import Flask, render_template, request, send_from_directory
import RPi.GPIO as GPIO #--- add back in
from enum import Enum
import paho.mqtt.client as mqtt

pi_ip_address='130.215.120.229'#'localhost'

# Initialise the PCA9685 using the default address (0x40).
pwm = Adafruit_PCA9685.PCA9685() #--- add back in
pwm.set_pwm_freq(60)#--- add back in

"""
Room Setup
"""
room_state = ""
curr_id = ''
passcodes = {"[0]": "12345", "[1]": "781911", "[2]": "43253416", "[3]": "MASTERY"}
state_ids = {"[0]": "'T_Door'", "[1]": ["'P_C2 + G_BD'", "'P_C2 + G_C2'", "'P_C2 + G_End'"],
             "[2]": ["'P_PP + G_C2'", "'P_C2 + G_C2'", "'P_End + G_C2'"], "[3]": "'M_FinalC'",}
promptingForPasscode = False
# correctPasscode = False

"""
START MQTT STUFF
"""
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("esp32/state")
    
def on_message(client, userdata, msg):
    global room_state
#     print("Message Received: " + msg.topic + " " + str(msg.payload)[1:])
    room_state = str(msg.payload)[1:]

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(pi_ip_address)
client.subscribe("esp32/state", 0)
client.loop_start()

import os     #importing os library so as to communicate with the system
os.system ("sudo pigpiod") #Launching GPIO library
time.sleep(1) # As i said it is too impatient and so if this delay is removed you will get an error
import pigpio #importing GPIO library

#TODO
#make it so that if it has not recieved anything from the html for a while, 
    #it stops moving

#usingCam = False #--- only for testing
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

class Toggle(Enum):
    TURN_OFF = -1 #is on, next press will turn off
    OFF = 0 # is off
    ON = 1 #is on
    TURN_ON = 2 #is off, next press will turn on
    
class LiftDirection(Enum):
    DOWN = -1
    NONE = 0
    UP = 1
# if(usingCam):    #--- only for testing
    # cam = RobtoCamTest.Camera() #--- only for testing
    
    
cam = RobtoCam.Camera() #--- add back in
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
move_speed = 1350  # Max pulse length out of 4096 #--- add back in
turn_speed = 1450 #--- add back in

servo_ctr = 320 #ultrasonic sensor facing front
LRservo_cur = servo_ctr
UDservo_cur = servo_ctr
LRcam_servo = 15 #left/right camera servo
UDcam_servo = 14 #up/down camera servo

maxRight = 120
maxLeft = 550
maxUp = 210
maxDown = 500
step = 5#20 #how far camera servos move in one step 
#TODO: test lowering step value, or maybe stepping less often

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
GPIO.setup(lightPin, GPIO.IN) #--- add back in

# For Lift
ESC=13  #Connect the ESC in this GPIO pin 
speed = 225 #TODO: adjust speed value, make slower so robot moves slower
stop = 1500

topLimitPin = 5
bottomLimitPin = 6
GPIO.setup(topLimitPin, GPIO.IN) #--- add back in
GPIO.setup(bottomLimitPin, GPIO.IN) #--- add back in

pi = pigpio.pi(); #--- add back in
time.sleep(1) #--- add back in
pi.set_servo_pulsewidth(ESC, stop) #--- add back in
        
        
def changespeed(speed):
    #print("changeSpeed") #--- only for testing
    pwm.set_pwm(ENB, 0, speed) #--- add back in
    pwm.set_pwm(ENA, 0, speed)#int(speed*.95)) #--- add back in

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
#         print(LRservo_cur)
        if LRservo_cur <= maxRight:
            LRservo_cur = maxRight            
        pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
    elif camDirX == CamDirection.LEFT.value:
        LRservo_cur = LRservo_cur + step #500
#         print(LRservo_cur)
        if LRservo_cur >= maxLeft:
            LRservo_cur = maxLeft            
        pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
    
    if camDirY == CamDirection.UP.value:
        UDservo_cur = UDservo_cur - step #120
#         print(UDservo_cur)
        if UDservo_cur <= maxUp:
            UDservo_cur = maxUp            
        pwm.set_pwm(UDcam_servo, 0, UDservo_cur)
    elif camDirY == CamDirection.DOWN.value:
        UDservo_cur = UDservo_cur + step #500
#         print(UDservo_cur)
        if UDservo_cur >= maxDown:
            UDservo_cur = maxDown            
        pwm.set_pwm(UDcam_servo, 0, UDservo_cur)

# --- PERIPHERAL FUNCTIONS ---
def centerCam():
#     print("centering cam")
    #return #--- only for testing
    global LRservo_cur, UDservo_cur
    LRservo_cur = servo_ctr
    UDservo_cur = servo_ctr 
    pwm.set_pwm(LRcam_servo, 0, LRservo_cur)
    pwm.set_pwm(UDcam_servo, 0, UDservo_cur)
    
def moveLift():
    global liftDir, buttonVals
    #return #--- only for testing
    checkLiftLimits()
    if(liftDir != LiftDirection.UP.value and buttonVals[7]==1):
        pi.set_servo_pulsewidth(ESC, stop-speed)
        if(liftDir == LiftDirection.DOWN.value):
            liftDir = LiftDirection.NONE.value 
    elif(liftDir != LiftDirection.DOWN.value and buttonVals[8]==1):
        pi.set_servo_pulsewidth(ESC, stop+speed)
        if(liftDir == LiftDirection.UP.value):
            liftDir = LiftDirection.NONE.value    
    else:
        pi.set_servo_pulsewidth(ESC, stop)
        
def checkLiftLimits():
    global liftDir
    if(GPIO.input(topLimitPin) == 0):
        liftDir = LiftDirection.UP.value
    elif(GPIO.input(bottomLimitPin) == 0):
        liftDir = LiftDirection.DOWN.value
    
def whiteFlashlight(status):
    if(status):
        pwm.set_pwm(whitePin, 0, 4000)
    else:
        pwm.set_pwm(whitePin, 0, 0)
    pwm.set_pwm(UVPin, 0, 0)
    
def uvFlashlight(status):
    if(status):
        pwm.set_pwm(UVPin, 0, 4000)    #switch leds on and off
    else:
        pwm.set_pwm(UVPin, 0, 0)
    pwm.set_pwm(whitePin, 0, 0)

def magnet(status):
    if(status):
        pwm.set_pwm(magnetPin, 0, 4000)    #switch EM on and off
    else:
        pwm.set_pwm(magnetPin, 0, 0)

#initialize robot
stopcar()
pwm.set_pwm(LRcam_servo, 0, servo_ctr) #--- add back in
pwm.set_pwm(UDcam_servo, 0, servo_ctr) #--- add back in
time.sleep(2)

running = True

carDir = CarDirection.NONE.value

camDirX = CamDirection.NONE.value
camDirY = CamDirection.NONE.value
cam_center = False
buttonVals = [0,0,0,0,0,0,0,0,0]
#Buttons:
#0:
#1: 
#2:
#3: UV flashlight toggle
#4: White flashlight toggle
#5: Center cam
#6: Electromagnet toggle
#7: Lift up
#8: Lift down
class ButtonNum(Enum):
    UV  = 3
    FLASH = 4
    CENTER = 5
    EM = 6
    LIFT_UP = 7
    LIFT_DOWN = 8
#TODO: use ButtonNum.[button wanted].value instead of hard coded numbers!
    #so that if buttons change order, only have to change the code in this enum and nowhere else!!

prevButtons = [0,0,0,0,0,0,0,0,0]
prevButtonState = [0,0,0,0,0,0,0,0,0]
UVToggle = Toggle.OFF.value
flashlightToggle = Toggle.OFF.value
magnetToggle = Toggle.OFF.value
liftDir = LiftDirection.NONE.value
peripheralUpdates = True;
#waitingForUpdates = False;

def checkState():
    global room_state, passcodes, promptingForPasscode, state_ids, curr_id
    if(cam.markerCorners):
        arucoId, arucoDist = cam.get_closest_aruco()
        curr_id = arucoId
#         print(round(arucoDist,1), room_state)
        if(arucoDist >= 550):
            if(curr_id in passcodes):
                statesWithId = state_ids.get(curr_id)
                if(room_state in statesWithId):
                    print(True)
                    promptingForPasscode = True
            else:
                promptingForPasscode = False
        else:
                promptingForPasscode = False      
    else:
        promptingForPasscode = False
        
def checkPasscode():
    global correctPasscode
    if(correctPasscode):
        client.publish("rpi/passcode", "accepted")
        client.publish("rpi/aruco",curr_id)
    else:    
        correctPasscode = False
#     else:
#         client.publish("rpi/passcode", "denied")

camStepCount = 0
def update(dt):
    #TODO: prevent race conditions with Flask app changing values of buttons and axes?? 
    #maybe just set local variables equal to what the values were at the beginning of update?
    global UVToggle, flashlightToggle, magnetToggle, cam_center, buttonVals, camStepCount
    
    #see if in state requiring passcode
    checkState()
#     checkPasscode()
#     print(room_state)
    
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
#         if(camStepCount>=3  ):
#             camStepCount = 0
#             turnCam()
#         camStepCount += 1 
    
#     cam.set_terminal("default")
    #TODO: use button enums for the following, rather than hardcoded numbers 
     # Checks UV Flashlight
    if(UVToggle == Toggle.TURN_ON.value and buttonVals[3]==1):
        uvFlashlight(1)
        UVToggle = Toggle.ON.value
        flashlightToggle = Toggle.OFF.value
    elif(UVToggle == Toggle.ON.value and buttonVals[3]==0):
        UVToggle = Toggle.TURN_OFF.value
    elif(UVToggle == Toggle.TURN_OFF.value and buttonVals[3]==1):
        uvFlashlight(0)
        UVToggle = Toggle.OFF.value
    elif(UVToggle == Toggle.OFF.value and buttonVals[3]==0):
        UVToggle = Toggle.TURN_ON.value
        
    # Checks flashlight
    if(flashlightToggle == Toggle.TURN_ON.value and buttonVals[4]==1):
        whiteFlashlight(1)
        flashlightToggle = Toggle.ON.value
        UVToggle = Toggle.OFF.value
    elif(flashlightToggle == Toggle.ON.value and buttonVals[4]==0):
        flashlightToggle = Toggle.TURN_OFF.value
    elif(flashlightToggle == Toggle.TURN_OFF.value and buttonVals[4]==1):
        whiteFlashlight(0)
        flashlightToggle = Toggle.OFF.value
    elif(flashlightToggle == Toggle.OFF.value and buttonVals[4]==0):
        flashlightToggle = Toggle.TURN_ON.value

    # Check Camera Center Button    
    if(buttonVals[5]==1):
        cam_center = True
    else:
        cam_center = False         
            
    # Checks EM
    if(magnetToggle == Toggle.TURN_ON.value and buttonVals[6]==1):
        magnet(1)
        magnetToggle = Toggle.ON.value
    elif(magnetToggle == Toggle.ON.value and buttonVals[6]==0):
        magnetToggle = Toggle.TURN_OFF.value
    elif(magnetToggle == Toggle.TURN_OFF.value and buttonVals[6]==1):
        magnet(0)
        magnetToggle = Toggle.OFF.value
    elif(magnetToggle == Toggle.OFF.value and buttonVals[6]==0):
        magnetToggle = Toggle.TURN_ON.value 
        
    moveLift()
            
    # #Copies previous buttons
    # for i in range(9):
        # prevButtons[i] = buttonVals[i]
        
app = Flask(__name__, static_url_path='')


@app.route("/")
def hello():
   return render_template('testing.html')

# promptingForPasscode = False;
# currentPasscode = 0;
# 
# passcodeList = ["9435", "blah"];
   
from flask import Response
import json

@app.route("/sendPasscode")
def recievePasscode():
    global room_state, passcodes, promptingForPasscode, curr_id, correctPasscode
    passcodeInput = request.args.get('passcode');
    print(passcodeInput);
    data = [0,0];
    
    if(promptingForPasscode):
        data[0] = 1;#looking for passcode
    else:
        data[0] = 0;#not looking for passcode
        
    if(passcodeInput == passcodes[curr_id]):
        data[1] = 1; #correct passcode
        correctPasscode = True
    else:
        data[1] = 0; #incorrect passcode
        
    if(data[1]==1):
        client.publish("rpi/passcode", "accepted")
        client.publish("rpi/aruco",curr_id)
    else:
        client.publish("rpi/passcode", "denied") 
    return Response(json.dumps(data), mimetype = 'text/xml')
    
     
     
   #for peripheral continuous upates
   
   #Options other than SSE:
   #https://nitin15j.medium.com/push-over-http-ba42f2e1bdfc
   
   
   #https://maxhalford.github.io/blog/flask-sse-no-deps/
   #SERVER-SENT EVENT!! MAKE HTML LISTEN FOR UPDATES FROM FLASK!
   #PREVENT LAG AND TIMEOUTS FROM CONSTANT XML REQUESTS
   # import queue

    # class MessageAnnouncer:

        # def __init__(self):
            # self.listeners = []

        # def listen(self):
            # q = queue.Queue(maxsize=5)
            # self.listeners.append(q)
            # return q

        # def announce(self, msg):
            # for i in reversed(range(len(self.listeners))):
                # try:
                    # self.listeners[i].put_nowait(msg)
                # except queue.Full:
                    # del self.listeners[i]
@app.route("/ask")
def responding(): 
    #global countDebug
    #print(countDebug)
    #countDebug = countDebug+1;
    
    #text = "<bookstore><book>" + "<title>Everyday Italian</title>" + "<author>Giada De Laurentiis</author>" + "<year>2005</year>" +"</book></bookstore>";
    
    # if(waitingForUpdates):
        
    # while(!peripheralUpdates):
        # waitingForUpdates = True;
    # waitingForUpdates = False;
    
    data ={"peripherals": \
            {ButtonNum.UV.value: UVToggle, \
            ButtonNum.FLASH.value: flashlightToggle, \
            ButtonNum.EM.value: magnetToggle},\
        "prompt": promptingForPasscode,\
        "message": ""} 
        
        #"prompt", prompting for a passcode input 
        #"message", a message to the player to be displayed onscreen
    #print(data)

    #d['fish'] = 'wet'     # Set an entry in a dictionary
    #print(d['fish'])      # Prints "wet"
    
    #return render_template('testing.html', data=data, mimetype='text/xml');
    return Response(json.dumps(data), mimetype = 'application/json')#Response(data);#, mimetype='text/xml');
   
    # UVToggle = Toggle.OFF.value
    # flashlightToggle = Toggle.OFF.value
    # magnetToggle = Toggle.OFF.value
    # liftDir = LiftDirection.NONE.value
   # class ButtonNum(Enum):
    # UV  = 3
    # FLASH = 4
    # CENTER = 5
    # EM = 6
    # LIFT_UP = 7
    # LIFT_DOWN = 8
    
    
@app.route("/data")
def recieve1(): #buttonvals,moveAxesVal,camAxesVals):
    global carDir, camDirX, camDirY, buttonVals, prevButtonState, prevButtons, UVToggle, magnetToggle, flashlightToggle, center_cam
#     print("received")
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
    
    
    #make it so that up and down are mutually exclusive,
        #but if youre holding one and then hold the other, the more recent one takes priority,
        #and if you let go of the second, the first one takes over again?
        
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


#TODO: fix problem when right click image and "open image in new tab"
@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
#     if(usingCam):#--- only for testing
#         return Response(cam.start(), mimetype='multipart/x-mixed-replace; boundary=frame')#--- only for testing
#     else:#--- only for testing
#         return#--- only for testing
    return Response(cam.start(), mimetype='multipart/x-mixed-replace; boundary=frame') #--- add back in
        
class MqttThread(threading.Thread):
    global client
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event
        self.count = 0
        client.loop_start()

    def run(self):
        if(self.count == 1000):
            self.count = 0
            client.loop()
        else:
            self.count = self.count + 1
        
class MyThread(threading.Thread):
    def __init__(self, event):
        global count
        threading.Thread.__init__(self)
        self.stopped = event


    def run(self):
        old_time = time.time()
#         mqtt = MqttThread(self.stopped)
#         mqtt.daemon=True
#         mqtt.run()
        while not self.stopped.wait(.01):
            dt = time.time()-old_time
            update(dt)
            old_time = time.time()
            

def cleanup():
    print("ending")
    pwm.set_pwm(LRcam_servo, 0, servo_ctr)
    pwm.set_pwm(UDcam_servo, 0, servo_ctr)
    GPIO.cleanup()
    
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
#         print("starting")
        #atexit.register(cleanup)
        app.run(host=pi_ip_address, port=8000, debug=False)#set debug off??
    finally:
        cleanup()
 

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
