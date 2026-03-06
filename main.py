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

from robot_motion_interface import *
from stabilization import handle_stabilized_points
from vision_QR import calculate_object_position_3_dof


TEST_RUN = 1 # True == test (vision only) or False == run with robot
CONNECTION_INTERVAL = 0.5 # s
QR_TEXT = '001'
QR_POSITION = [110.0, 60.0, 400.0] # [x, y, z] mm
MAX_ALLOWED_OFFSET = 50 # mm
MIN_ALLOWED_OFFSET = 2 # mm
ALLOWED_SPEED = 30 # %


def run():

    # variables for time measurement
    i = 0
    last_time_fps = time.time()
    last_time_connection = time.time()

    # additional variables
    list_with_stabilized_objects = []
    sequence = 1 # ID of the motion command in RMI sequence

    # initializing QR code detector
    qr_detect = cv2.QRCodeDetector()

    # initializing webcam video capture
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Cannot open camera!")
        exit()

    if not TEST_RUN:
        sock = initialize_connection()
        # go to start position
        sequence = home_robot(sock, sequence, speed=ALLOWED_SPEED)
    
    # start a while loop
    while(True):

        # reading the video from the webcam in image frames
        is_frame, image_original_frame = webcam.read()
        image_processed = image_original_frame.copy()

        # detect QR codes
        decoded_text, vertices_coords, binarized_straight_qrcode = qr_detect.detectAndDecode(image_original_frame)

        if decoded_text[:3] == QR_TEXT:
            raw_coord = calculate_object_position_3_dof(vertices_coords[0])
            # x, y, z = raw_coord
            # print("{:.2f}".format(x), "{:.2f}".format(y), "{:.2f}".format(z))

            list_with_stabilized_objects, stabilized_coords = handle_stabilized_points(
                                                                list_with_stabilized_objects, [raw_coord]) 
            # draw outlines of the codes
            image_processed = cv2.polylines(image_original_frame, vertices_coords.astype(int), True, (0, 255, 0), 3)

        else:
            list_with_stabilized_objects, stabilized_coords = handle_stabilized_points(
                                                                list_with_stabilized_objects, [])

        # draw window
        cv2.imshow("QR Detection in Real-TIme", image_processed)

        # connection
        if time.time() > last_time_connection + CONNECTION_INTERVAL:
            last_time_connection = time.time()

            if len(stabilized_coords):
                position_offset = [round(float(q1 - q2), 2) for (q1, q2) in zip(QR_POSITION, stabilized_coords[0])]
                print(stabilized_coords[0])
            else:
                position_offset = [0, 0, 0]
            print(position_offset)
                           
            if not TEST_RUN and math.dist(position_offset, [0, 0, 0]) < MAX_ALLOWED_OFFSET \
                            and math.dist(position_offset, [0, 0, 0]) > MIN_ALLOWED_OFFSET:
                sequence = move_robot_cartesian_representation(sock, sequence, is_motion_relative=True, 
                                                #x = position_offset[2],
                                                y = position_offset[0], 
                                                z = position_offset[1], 
                                                wait_for_response = not sequence % 5)

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
    if not TEST_RUN:
        close_connection(sock)
    webcam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()