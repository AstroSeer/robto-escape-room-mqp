# author: abmoore
# last edit: 18-Jan-2022
#
# This is the pi camera class. All we have to do to use
#   it is instantiate it and call the start() method.
from asyncio.windows_events import NULL
from flask import Flask, render_template, Response


from picamera.array import PiRGBArray  #--- add back in
from picamera import PiCamera as pc #--- add back in 
import time
import cv2
import numpy as np

time.sleep(0.1)  

class Camera:
    #app = Flask(__name__)
    def __init__(self):
        self.video = cv2.VideoCapture(0) #--- add back in
        #self.video = cv2.VideoCapture(2, cv2.CAP_DSHOW) #only for testing
        
        # video.set(cv2.CAP_PROP_FPS, 70) #sets FPS
        # video.set(3, 640) #sets first resolution
        # video.set(4, 480) #sets second resolution
        self.video.set(cv2.CAP_PROP_BUFFERSIZE, 5)

        self.frame = NULL
        self.markerCorners = NULL
        self.markerIds = NULL
        
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
            self.frame = rotated_img           
            #sets camera to recognize aruco markers
            dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
            parameters= cv2.aruco.DetectorParameters_create()         
            #detects marker corners and IDs
            markerCorners, markerIds, rejectedCandidates = cv2.aruco.detectMarkers(self.frame, dictionary, parameters = parameters)
            self.markerCorners = markerCorners
            self.markerIds = markerIds         
            #print(markerIds)
            
            #draws markers on camera
            rotated_img = cv2.aruco.drawDetectedMarkers(self.frame, markerCorners, markerIds)           
            
            #gets perimeter of detected marker
            aruco_perimeter = cv2.arcLength(markerCorners[0], True)
            print(aruco_perimeter)


            #makes image bigger
            rotated_img = self.rescale(self.frame, 70) 
            
            #displays frame
            #cv2.imshow("Frame", rotated_img)
            #saves frame
        #     cv2.imwrite("led_test.jpg", rotated_img)
            success, buffer = cv2.imencode('.jpg', self.frame)
            fram = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + fram + b'\r\n')  # concat frame one by one and show result
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

    def set_terminal(self, state):
        if(state is "accepted"):
            terminal_status = cv2.imread("terminal/PWD_GOOD2.png")
        elif(state is "denied"):
            terminal_status = cv2.imread("terminal/PWD_BAD2.png")
        else:
            terminal_status = cv2.imread("terminal/PWD_START.png")

        index = np.squeeze(self.markerIds[0])
        refPt1 = np.squeeze(self.markerCorners[index[0]])[1]
        
        index = np.squeeze(self.markerIds[1])
        refPt2 = np.squeeze(self.markerCorners[index[0]])[2]

        distance = np.linalg.norm(refPt1-refPt2)
        
        scalingFac = 0.02
        pts_dst = [[refPt1[0] - round(scalingFac*distance), refPt1[1] - round(scalingFac*distance)]]
        pts_dst = pts_dst + [[refPt2[0] + round(scalingFac*distance), refPt2[1] - round(scalingFac*distance)]]
        
        index = np.squeeze(self.markerIds[2])
        refPt3 = np.squeeze(self.markerCorners[index[0]])[0]
        pts_dst = pts_dst + [[refPt3[0] + round(scalingFac*distance), refPt3[1] + round(scalingFac*distance)]]

        index = np.squeeze(self.markerIds[3])
        refPt4 = np.squeeze(self.markerCorners[index[0]])[0]
        pts_dst = pts_dst + [[refPt4[0] - round(scalingFac*distance), refPt4[1] + round(scalingFac*distance)]]

        pts_src = [[0,0], [terminal_status.shape[1], 0], [terminal_status.shape[1], terminal_status.shape[0]], [0, terminal_status.shape[0]]]
        
        pts_src_m = np.asarray(pts_src)
        pts_dst_m = np.asarray(pts_dst)
        
        # Calculate Homography
        h, status = cv2.findHomography(pts_src, pts_dst)
        # Warp source image to destination based on homography
        warped_image = cv2.warpPerspective(terminal_status, h, (self.frame.shape[1],self.frame.shape[0]))
        
        # Prepare a mask representing region to copy from the warped image into the original frame
        mask = np.zeros([self.frame.shape[0], self.frame.shape[1]], dtype=np.uint8)
        cv2.fillConvexPoly(mask, np.int32([pts_dst_m]), (255, 255, 255), cv2.LINE_AA)

        # Erode the mask to not copy the boundary effects from the warping
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        mask = cv2.erode(mask, element, iterations=3)

        # Copy the mask into 3 channels.
        warped_image = warped_image.astype(float)
        mask3 = np.zeros_like(warped_image)
        for i in range(0, 3):
	        mask3[:,:,i] = mask/255

        # Copy the masked warped image into the original frame in the mask region
        warped_image_masked = cv2.multiply(warped_image, mask3)
        frame_masked = cv2.multiply(frame.astype(float), 1-mask3)
        self.frame = cv2.add(warped_image_masked, frame_masked)

    
# c = Camera()
# c.start()
