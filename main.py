# Vision Robot 2026
# By Tomasz Golaszewski
# 12.2025 -


import os
import cv2
import numpy as np
import time
import math

from sys import path

# check the system and add files to path
if os.name == "posix":
    path.append('./src')
    print("Linux")
elif os.name == "nt":
    path.append('.\\src')
    print("Windows")
else:
    path.append('.\\src')
    print("other")

from vision_QR import calculate_object_position_3_dof
from robot_motion_interface import *

CONNECTION_INTERVAL = 0.5


def run():

    # variables for time measurement
    i = 0
    last_time_fps = time.time()
    last_time_connection = time.time()

    # initializing QR code detector
    qr_detect = cv2.QRCodeDetector()

    # initializing webcam video capture
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Cannot open camera!")
        exit()

    # start a while loop
    while(True):

        # reading the video from the webcam in image frames
        is_frame, image_original_frame = webcam.read()
        image_processed = image_original_frame.copy()

        # detect QR codes
        is_code, vertices_coords = qr_detect.detect(image_original_frame)

        if is_code:
            x, y, z = calculate_object_position_3_dof(vertices_coords[0])
            print("---")
            print(x, y, z)
            print("{:.2f}".format(x), "{:.2f}".format(y), "{:.2f}".format(z))

            # draw outlines of the codes
            image_processed = cv2.polylines(image_original_frame, vertices_coords.astype(int), True, (0, 255, 0), 3)

        # draw window
        cv2.imshow("QR Detection in Real-TIme", image_processed)

        # connection
        if time.time() > last_time_connection + CONNECTION_INTERVAL:
            last_time_connection = time.time()
            print("conn")

        # measure time
        if time.time() > last_time_fps + 1:
            last_time_fps = time.time()
            print("FPS:", i)
            i = 0
        else:
            i += 1

        # program termination
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    
    # clean up
    webcam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()