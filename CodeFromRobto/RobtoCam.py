# author: abmoore
# last edit: 18-Jan-2022
#
# This is the pi camera class. All we have to do to use
#   it is instantiate it and call the start() method.

from picamera.array import PiRGBArray
from picamera import PiCamera as pc
import time
import cv2
import numpy as np

time.sleep(0.1)  

class Camera:
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        # video.set(cv2.CAP_PROP_FPS, 70) #sets FPS
        # video.set(3, 640) #sets first resolution
        # video.set(4, 480) #sets second resolution
        self.video.set(cv2.CAP_PROP_BUFFERSIZE, 5)
        
        if not self.video.isOpened():
            print("cannot open video")
            exit()

    def rescale(self, image, percent):
        width = int(image.shape[1] * percent/100)
        height = int(image.shape[0] * percent/100)
        dim= (width, height)
        return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

    def start(self):
        while True:
            ret, frame = self.video.read()
            
            if not ret:
                print("no feed ", ret)
                break
            #rotates image 180 degrees
            rotated_img = cv2.rotate(frame, cv2.ROTATE_180)           
            #sets camera to recognize aruco markers
            dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
            parameters= cv2.aruco.DetectorParameters_create()         
            #detects marker corners and IDs
            markerCorners, markerIds, rejectedCandidates = cv2.aruco.detectMarkers(rotated_img, dictionary, parameters = parameters)         
            #draws markers on camera
            rotated_img = cv2.aruco.drawDetectedMarkers(rotated_img, markerCorners, markerIds)           
            #makes image bigger
            rotated_img = self.rescale(rotated_img, 150)          
            #displays frame
            cv2.imshow("Frame", rotated_img)
            #saves frame
        #     cv2.imwrite("led_test.jpg", rotated_img)
            
            if cv2.waitKey(1) == ord('q'):
                break
        self.video.release()
        cv2.destroyAllWindows()

c = Camera()
c.start()