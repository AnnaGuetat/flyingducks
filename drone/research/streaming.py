#!/usr/bin/env python

import cv2
import math
import tempfile

import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, Landing
from olympe.messages.ardrone3.Piloting import moveBy
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged
from olympe.messages.ardrone3.Camera import Orientation
from olympe.messages.ardrone3.CameraState import Orientation as StateOrientation
import olympe_deps as od

# NOTE: from Parrot Olympe repository


class StreamingExample:

    def __init__(self):
        # Create the olympe.Drone object from its IP address
        self.drone = olympe.Drone(
            "192.168.42.1",
            loglevel=3,
            drone_type=od.ARSDK_DEVICE_TYPE_BEBOP_2,
        )
        self.tempd = tempfile.mkdtemp(prefix="olympe_streaming_test_")
        print("Olympe streaming example output dir: {}".format(self.tempd))

    def start(self):
        # Connect the the drone
        self.drone.connection()

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
        cv2frame = cv2.cvtColor(yuv_frame.as_ndarray(), cv2_cvt_color_flag)

        # Use OpenCV to show this frame
        cv2.imshow("Parrot Bebop 2 FPV", cv2frame)
        cv2.waitKey(1)  # please OpenCV for 1 ms...

    def fly(self):
        # Takeoff, fly, land, ...
        print("Takeoff")
        self.drone(
            TakeOff()
            & FlyingStateChanged(
            state="hovering", _timeout=10, _policy="check_wait")
                ).wait()
        self.drone(Orientation(pan=0, tilt=0) & StateOrientation(pan=0, tilt=0)).wait().success()

        for i in range(2):
            print("Moving by ({}/2)...".format(i + 1))
            self.drone(moveBy(0, 0, 0, math.pi, _timeout=20)).wait().success()

        print("Landing...")
        self.drone(Orientation(pan=0, tilt=-82) & StateOrientation(pan=0, tilt=-82)).wait().success()
        self.drone(
            Landing()
            >> FlyingStateChanged(state="landed", _timeout=5)
        ).wait()
        print("Landed\n")


if __name__ == "__main__":
    streaming_example = StreamingExample()
    # Start the video stream
    streaming_example.start()
    # Perform some live video processing while the drone is flying
    streaming_example.fly()
    streaming_example.stop()
