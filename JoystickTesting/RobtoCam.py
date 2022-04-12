# author: abmoore
# last edit: 18-Jan-2022
#
# This is the pi camera class. All we have to do to use
#   it is instantiate it and call the start() method.
# from flask import Flask, render_template, Response
from paho.mqtt import client
from picamera.array import PiRGBArray  #--- add back in
from picamera import PiCamera as pc #--- add back in 
import time
import cv2
import numpy as np

time.sleep(0.1)  

class Camera:
    #app = Flask(__name__)
    def __init__(self):
        self.video = cv2.VideoCapture(0) 
        #self.video = cv2.VideoCapture(2, cv2.CAP_DSHOW) #only for testing
        
        self.video.set(cv2.CAP_PROP_FPS, 32) #sets FPS
        self.video.set(3, 768) #sets first resolution
        self.video.set(4, 432) #sets second resolution
        self.video.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.frame = None
        self.markerCorners = None
        self.markerIds = None
        self.terminalState = "default"
        
        if not self.video.isOpened():
            print("cannot open video")
            exit()

    def rescale(self, image, percent):
        width = int(image.shape[1] * percent/100)
        height = int(image.shape[0] * percent/100)
        dim = (width, height)
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
            self.frame = rotated_img
            self.frame = self.rescale(self.frame, 70) 
            #sets camera to recognize aruco markers
            dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
            parameters= cv2.aruco.DetectorParameters_create()         
            #detects marker corners and IDs
            markerCorners, markerIds, rejectedCandidates = cv2.aruco.detectMarkers(self.frame, dictionary, parameters = parameters)
            self.markerCorners = markerCorners
            self.markerIds = markerIds         
            #print(markerIds)
            
            #draws markers on camera
#             self.frame = cv2.aruco.drawDetectedMarkers(self.frame, markerCorners, markerIds)           
#             corners = np.int0(self.markerCorners)
#             cv2.polylines(self.frame, corners, True, (0, 255, 0), 5)
            #gets perimeter of detected marker
#             if(markerCorners):
#                 aid, aruco_size = self.get_closest_aruco()
#                 side = aruco_size/4
#                 cv2.putText(self.frame, "Perimeter: {} px".format(round(aruco_size, 1)), (int(25), int(35)), cv2.FONT_HERSHEY_PLAIN, 2, (100,200,0), 2)
#                 cv2.putText(self.frame, "ID: {}".format(aid), (int(25), int(80)), cv2.FONT_HERSHEY_PLAIN, 2, (100,200,0), 2)

            aid, aruco_size = self.get_closest_aruco()    
            if(len(self.markerCorners) == 1) and (aruco_size > 100):
                self.set_terminal(aruco_size)
                 

            #makes image bigger
#             self.frame = self.rescale(self.frame, 70) 
            
            #displays frame
            cv2.imshow("Frame", self.frame)
            #saves frame
            cv2.imwrite("poster_pic.jpg", self.frame)
#             success, buffer = cv2.imencode('.jpg', self.frame)
#             fram = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + fram + b'\r\n')  # concat frame one by one and show result
            if cv2.waitKey(1) == ord('q'):
                break
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

    def get_closest_aruco(self):
        dist = 0
        arucoID = 0
        for i in self.markerIds:
            aruco_size = cv2.arcLength(self.markerCorners[0], True)
            if(aruco_size > dist):
                dist = aruco_size
                arucoID = i
        return arucoID, dist    

    def set_terminal(self, aruco_size):
        if(self.terminalState is "accepted"):
            terminal_status = "Password Accepted"#cv2.imread("terminal/PWD_GOOD2.png")
        elif(self.terminalState is "denied"):
            terminal_status = "Password Denied"#cv2.imread("terminal/PWD_BAD2.png")
        else:
            terminal_status = "Enter'\n'Password"#cv2.imread("terminal/PWD_START.png")


        index = np.squeeze(np.where(self.markerIds==0))
        refPt1 = np.squeeze(self.markerCorners[index[0]])[0]
        refPt2 = np.squeeze(self.markerCorners[index[0]])[1]
        refPt3 = np.squeeze(self.markerCorners[index[0]])[2]
        refPt4 = np.squeeze(self.markerCorners[index[0]])[3]

        scaling_factor = 6
        pts_dst = [[refPt1[0]-aruco_size/scaling_factor, refPt1[1]-aruco_size/scaling_factor],
                   [refPt2[0]+aruco_size/scaling_factor, refPt2[1]-aruco_size/scaling_factor],
                   [refPt3[0]+aruco_size/scaling_factor, refPt3[1]+aruco_size/scaling_factor],
                   [refPt4[0]-aruco_size/scaling_factor, refPt4[1]+aruco_size/scaling_factor]]

        pts_dst_m = np.array(pts_dst)
        cv2.fillPoly(self.frame, np.int32([pts_dst_m]), (0,0,0))
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        textSize = cv2.getTextSize(terminal_status, font, 1,2)[0]
        poly_center = np.int32([refPt1[0], # + np.round((refPt2[0]-refPt1[0])/2)) + textSize[0])/2,
                                refPt1[1]])# + np.round((refPt4[1]-refPt1[1])/2)) + textSize[1])/2])
        cv2.putText(self.frame, "ENTER", np.int32([refPt1[0], refPt1[1]+5]), font, 0.5, (0,255,0), 2, cv2.LINE_AA)
        cv2.putText(self.frame, "PASSWORD", np.int32([refPt1[0]-17, refPt1[1]+25]), font, 0.5, (0,255,0), 2, cv2.LINE_AA)
        
#         # Calculate Homography
#         h, status = cv2.findHomography(pts_src_m, pts_dst_m)
#         # Warp source image to destination based on homography
#         warped_image = cv2.warpPerspective(terminal_status, h, (self.frame.shape[1], self.frame.shape[0]))
        
#         # Prepare a mask representing region to copy from the warped image into the original frame
#         mask = np.zeros([self.frame.shape[0], self.frame.shape[1]], dtype=np.uint8)
#         cv2.fillConvexPoly(mask, np.int32([pts_dst_m]), (255, 255, 255), cv2.LINE_AA)
# 
#         # Erode the mask to not copy the boundary effects from the warping
#         element = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
#         mask = cv2.erode(mask, element, iterations=3)
# 
#         # Copy the mask into 3 channels.
#         warped_image = warped_image.astype(float)
#         mask3 = np.zeros_like(warped_image)
#         for i in range(0, 3):
#             mask3[:,:,i] = mask/255

        # Copy the masked warped image into the original frame in the mask region
#         warped_image_masked = cv2.multiply(warped_image, mask3)
#         frame_masked = cv2.multiply(self.frame.astype(float), 1-mask3)
#         self.frame = cv2.add(warped_image, self.frame)

    
c = Camera()
c.start()