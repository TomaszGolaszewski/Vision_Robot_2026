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

from settings import *
from robot_motion_interface import *
from robot_motion_tcp_client import *
from stabilization import handle_stabilized_points
from vision_QR import calculate_object_position_3_dof



def run():

    # variables for time measurement
    i = 0
    last_time_fps = time.time()
    last_time_connection = time.time()

    # robot variables
    robot_current_position = [0, 0, 0, 0, 0, 0]
    robot_current_forces = [0, 0, 0, 0, 0, 0]
    sequence_queue = []
    sequence = 1 # ID of the motion command in RMI sequence

    # additional variables
    list_with_stabilized_objects = []

    # initializing QR code detector
    qr_detect = cv2.QRCodeDetector()

    # initializing webcam video capture
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Cannot open camera!")
        exit()

    if not TEST_VISION:
        client = initialize_connection_with_tcp_client()
        # go to start position
        sequence = home_robot_with_tcp_client(client, sequence, speed=ALLOWED_SPEED)
    
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
                print("[COORDS]", stabilized_coords[0])
            else:
                position_offset = [0, 0, 0]
            print("[OFFSET]", position_offset, "=>",  round(math.dist(position_offset, [0, 0, 0]), 2))
            
            # get all messages, remove complited sequences from queue
            if not TEST_VISION:
                request_status(client)
                time.sleep(0.02) # time needed to receive response
                sequence_queue = get_and_handle_message_for_robot_motion(client, 
                            robot_current_position, robot_current_forces, sequence_queue)
                    
                print("[QUEUE]", len(sequence_queue), sequence_queue)
                print("[POSITION]", robot_current_position)
                # print("[FORCES]", robot_current_forces)

                # send new command
                if len(sequence_queue) < SEQUENCE_MAX_LENGTH \
                                and math.dist(position_offset, [0, 0, 0]) < MAX_ALLOWED_OFFSET \
                                and math.dist(position_offset, [0, 0, 0]) > MIN_ALLOWED_OFFSET:
                    sequence_queue.append(sequence)
                    sequence = move_robot_cartesian_representation_with_tcp_client(client, sequence, 
                                                    x = robot_current_position[0],# - position_offset[2],
                                                    y = robot_current_position[1] + position_offset[0], 
                                                    z = robot_current_position[2] + position_offset[1],
                                                    w = robot_current_position[3],
                                                    p = robot_current_position[4],
                                                    r = robot_current_position[5],
                                                    is_motion_relative=False, accuracy='CNT')

                print("[QUEUE]", len(sequence_queue), sequence_queue)

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
    if not TEST_VISION:
        time.sleep(1)
        sequence_queue = get_and_handle_message_for_robot_motion(client, 
                    robot_current_position, robot_current_forces, sequence_queue)
        print("[QUEUE]", len(sequence_queue), sequence_queue)

        close_connection_with_tcp_client(client)
    webcam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()