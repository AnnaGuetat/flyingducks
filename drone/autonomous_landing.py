#!/usr/bin/env python

import cv2
from cv2 import aruco
import math
import tempfile
import numpy as np
import logging

import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, Landing, PCMD, moveBy, CancelMoveBy
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged
from olympe.messages.ardrone3.Camera import Orientation
from olympe.messages.ardrone3.CameraState import Orientation as StateOrientation
import olympe_deps as od

# NOTE: from Parrot Olympe repository


class DronePreciseLanding:

    def __init__(self):
        # Create the olympe.Drone object from its IP address
        logging.basicConfig(format='%(asctime)s %(message)s')
        self.drone = olympe.Drone(
            "192.168.42.1",
            loglevel=1,
            drone_type=od.ARSDK_DEVICE_TYPE_BEBOP_2,
        )
        self.tempd = tempfile.mkdtemp(prefix="olympe_streaming_test_")
        print("Olympe streaming example output dir: {}".format(self.tempd))
        self.cv2frame = None
        self.landing = False
        self.contour = None

        self.aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_250)
        self.aruco_params = aruco.DetectorParameters_create()
        self.corners = None
        self.ids = []
        self.rejectedImgPoints = None

    def start(self):
        # Connect the the drone
        self.drone.connection()
        self.drone(Orientation(pan=0, tilt=0) & StateOrientation(pan=0, tilt=0)).wait().success()

        # You can record the video stream from the drone if you plan to do some
        # post processing.
        # Here, we don't record the (huge) raw YUV video stream
        # raw_data_file=os.path.join(self.tempd,'raw_data.bin'),
        # raw_meta_file=os.path.join(self.tempd,'raw_metadata.json'),


        # Setup your callback functions to do some live video processing
        self.drone.set_streaming_callbacks(
            raw_cb=self.yuv_frame_cb,
        )
        # Start video streaming
        self.drone.start_video_streaming()

    def stop(self):
        # Properly stop the video stream and disconnect
        self.drone.stop_video_streaming()
        cv2.destroyAllWindows()
        self.drone.disconnection()

    def yuv_frame_cb(self, yuv_frame):
        """
        This function will be called by Olympe for each decoded YUV frame.

            :type yuv_frame: olympe.VideoFrame
        """
        # the VideoFrame.info() dictionary contains some useful informations
        # such as the video resolution
        info = yuv_frame.info()
        height, width = info["yuv"]["height"], info["yuv"]["width"]

        # convert pdraw YUV flag to OpenCV YUV flag
        cv2_cvt_color_flag = {
            olympe.PDRAW_YUV_FORMAT_I420: cv2.COLOR_YUV2BGR_I420,
            olympe.PDRAW_YUV_FORMAT_NV12: cv2.COLOR_YUV2BGR_NV12,
        }[info["yuv"]["format"]]

        # yuv_frame.as_ndarray() is a 2D numpy array with the proper "shape"
        # i.e (3 * height / 2, width) because it's a YUV I420 or NV12 frame

        # Use OpenCV to convert the yuv frame to RGB
        self.cv2frame = cv2.cvtColor(yuv_frame.as_ndarray(), cv2_cvt_color_flag)

        img = cv2.cvtColor(self.cv2frame, cv2.COLOR_BGR2GRAY)
        if self.landing:
            self.corners, self.ids, self.rejectedImgPoints = aruco.detectMarkers(img, self.aruco_dict, parameters=self.aruco_params)
            img = aruco.drawDetectedMarkers(img, self.corners, self.ids)
            if self.ids is None:
                self.ids = []
            for i in range(len(self.ids)):
                c = self.corners[i][0]
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Grayscale", img)
        cv2.waitKey(1)
        # Use OpenCV to show this frame
        cv2.imshow("Parrot Bebop 2 FPV", self.cv2frame)
        cv2.waitKey(1)  # please OpenCV for 1 ms...

    def land(self):
        from time import sleep
        self.landing = True
        maxsize = 0
        no_mark_count = 0
        rotated = 0
        while self.landing:
            if self.corners is not None:
                for i in self.corners:

                    adj_location = False
                    f_b = 0
                    l_r = 0
                    rotated = 0
                    no_mark_count = 0
                    c = i
                    x, y, w, h = cv2.boundingRect(c)
                    maxsize = cv2.contourArea(c)
                    if maxsize > self.cv2frame.shape[0] * self.cv2frame.shape[1] * 0.065:
                        print('Landing pad below drone -> engines off')
                        self.drone(
                            Landing()
                            >> FlyingStateChanged(state="landed", _timeout=5)
                        ).wait().success()
                        self.landing = False
                        break
                    print(maxsize)
                    from_top = y-50
                    from_left = x
                    from_bottom = self.cv2frame.shape[0]-y-h
                    from_right = self.cv2frame.shape[1]-x-w
                    top_bot_diff = from_top-from_bottom
                    if abs(top_bot_diff) >100:
                        if top_bot_diff>0:
                            print('Need to move backward')
                            f_b = -1
                            adj_location = True
                        else:
                            print('Need to move forward')
                            f_b = 1
                            adj_location = True

                    left_right_diff = from_left-from_right
                    if abs(left_right_diff) >150:
                        if left_right_diff>0:
                            print('Need to move right')
                            l_r = 1
                            adj_location = True
                        else:
                            print('Need to move left')
                            l_r = -1
                            adj_location = True

                    if adj_location:
                        dist_adj = max([maxsize/(self.cv2frame.shape[0]*self.cv2frame.shape[1]*0.22),0.5])
                        self.drone(CancelMoveBy()) >> self.drone(moveBy(dist_adj*f_b*0.3, dist_adj*l_r*0.3, 0, 0, _timeout=20)).wait().success()
                    else:
                        #self.drone(Orientation(pan=0, tilt=-82) & StateOrientation(pan=0, tilt=-82)).wait().success()
                        print('On spot - lowering')
                        self.drone(moveBy(0, 0, 0.3, 0, _timeout=20)).wait().success()
                else:
                    no_mark_count += 1
                    if no_mark_count > 5:
                        print("Nothing detected - rotating")
                        self.drone(moveBy(0, 0, 0, math.pi/2, _timeout=20)).wait().success()
                        rotated += 1
                        #if rotated > 4:
                        #    self.drone(Orientation(pan=0, tilt=-60) & StateOrientation(pan=0, tilt=-60)).wait().success()
                    #else:
                        #if StateOrientation(pan=0,tilt=-82):
                    #        print('aaaa')
                    #        self.drone(Orientation(pan=0, tilt=-82) & StateOrientation(pan=0, tilt=-82)).wait().success()
            sleep(1)
        return True

    def fly(self):
        # Takeoff, fly, land, ...
        print("Takeoff")
        self.drone(
            TakeOff()
            & FlyingStateChanged(
                state="hovering", _timeout=10, _policy="check_wait")
        ).wait()
        #for i in range(2):
        #    print("Moving by ({}/2)...".format(i + 1))
        self.drone(moveBy(1, 0, -0.5, 0, _timeout=20)).wait().success()

        print("Landing...")
        self.drone(Orientation(pan=0, tilt=-82) & StateOrientation(pan=0, tilt=-82)).wait().success()
        self.land()
        print("Landed\n")


if __name__ == "__main__":
    streaming_example = StreamingExample()
    # Start the video stream
    streaming_example.start()
    # Perform some live video processing while the drone is flying
    streaming_example.fly()
    streaming_example.stop()
