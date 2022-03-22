# author: abmoore
# last edit: 18-Jan-2022
#
# This is the pi camera class. All we have to do to use
#   it is instantiate it and call the start() method.
from flask import Flask, render_template, Response

# from paho.mqtt import client #--- add back in
# from picamera.array import PiRGBArray  #--- add back in
# from picamera import PiCamera as pc #--- add back in 
import time
import cv2
import numpy as np

time.sleep(0.1)  

class Camera:
    #app = Flask(__name__)
    def __init__(self):
        self.video = cv2.VideoCapture(0)
#         self.video = cv2.VideoCapture(2, cv2.CAP_DSHOW) #only for testing
        # video.set(cv2.CAP_PROP_FPS, 70) #sets FPS
        self.video.set(3, 426) #sets first resolution
        self.video.set(4, 240) #sets second resolution
        self.video.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not self.video.isOpened():
            print("cannot open video")
            exit()

    def rescale(self, image, percent):
        width = int(image.shape[1] * percent/100)
        height = int(image.shape[0] * percent/100)
        dim= (width, height)
        return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

    def start(self):
        # if __name__ == '__main__':
            # app.run(debug=True)
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
            #print(markerIds)
            
            #draws markers on camera
            rotated_img = cv2.aruco.drawDetectedMarkers(rotated_img, markerCorners, markerIds)           
            #makes image bigger
            
            #rotated_img = self.rescale(rotated_img, 150) #increasing size makes camera feed slow down on html
            #rotated_img = self.rescale(rotated_img, 80) 
            rotated_img = self.rescale(rotated_img, 70) #might not need to reduce size?
                  
            #displays frame
            cv2.imshow("Frame", rotated_img)
            #saves frame
        #     cv2.imwrite("led_test.jpg", rotated_img)
#             success, buffer = cv2.imencode('.jpg', rotated_img)
#             fram = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + fram + b'\r\n')  # concat frame one by one and show result
            #if cv2.waitKey(1) == ord('q'):
             #   break
        self.video.release()
        cv2.destroyAllWindows()
    
    # @app.route('/video_feed')
    # def video_feed():
        # #Video streaming route. Put this in the src attribute of an img tag
        # return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


    # @app.route('/')
    # def index():
        # """Video streaming home page."""
        # return render_template('testing.html')


    
#c = Camera()
#c.start()