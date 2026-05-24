# Vision Robot 2026
# By Tomasz Golaszewski
# 12.2025 -


import os
import cv2
import numpy as np
import time
import math

from sys import path
from pyzbar.pyzbar import decode

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
from draw_graph_2D import plot_data
from draw_graph_2D import COLOR_DICT_GREY_LIME_ORANGE, COLOR_DICT_GREY_GREEN_RED
from draw_graph_3D import plot_3d_trajectories


def run():

    # variables for time measurement
    i = 0
    start_time = time.time()
    last_time_fps = time.time()
    last_time_connection = time.time()# + WARM_UP_SKIP_TIME

    # robot variables
    robot_current_position = [0, 0, 0, 0, 0, 0]
    robot_current_forces = [0, 0, 0, 0, 0, 0]
    sequence_queue = []
    sequence = 1 # ID of the motion command in RMI sequence

    # history
    history_time = []
    history_robot_position = []
    history_target_position = []
    history_kalman_measurement = []
    history_kalman_prediction = []

    # Kalman filter initialization
    kalman = cv2.KalmanFilter(6, 3)  # 6 dynamic params, 3 measurement params

    # state: [x, y, z, vx, vy, vz]
    # F - the state-transition model
    # A - macierz systemowa ukladu (macierz przejscia)
    kalman.transitionMatrix = np.array([
        [1, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 1, 0],
        [0, 0, 1, 0, 0, 1],
        [0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 1]
    ], np.float32)

    kalman.measurementMatrix = np.array([
        [1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0]
    ], np.float32)

    kalman.processNoiseCov = np.eye(6, dtype=np.float32) * 0.03
    kalman.measurementNoiseCov = np.eye(3, dtype=np.float32) * 0.5

    measurement = np.zeros((3, 1), np.float32)
    prediction = np.zeros((3, 1), np.float32)

    # initializing webcam video capture
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Cannot open camera!")
        exit()

    if not TEST_VISION:
        client = initialize_connection_with_tcp_client()
        # go to start position
        sequence = home_robot_with_tcp_client(client, sequence, speed=ALLOWED_SPEED)
    
    # restart time
    start_time = time.time()

    # start a while loop
    while True:

        if not TEST_VISION:
            request_status(client)

        # reading the video from the webcam in image frames
        is_frame, image_original_frame = webcam.read()
        image_processed = image_original_frame.copy()
  
        # detect QR codes using pyzbar
        decoded_objects = decode(image_original_frame)

        # Kalman filter update
        # prediction = kalman.predict()
        # pred_x, pred_y, pred_z = int(prediction[0][0]), int(prediction[1][0]), int(prediction[2][0])

        is_valid_code_detected = False
        for obj in decoded_objects:
            if obj.data.decode()[:3] == QR_TEXT:
                is_valid_code_detected = True

                # calculate the coordinates of the QR code relative to the camera
                vertices_coords = np.array([[p.x, p.y] for p in obj.polygon], dtype=np.int32)
                raw_coord = calculate_object_position_3_dof(vertices_coords)
                raw_qr_global_coords = raw_coord

                # draw outlines of the codes
                image_processed = cv2.polylines(image_original_frame, [vertices_coords], True, (0, 255, 0), 3)

        # draw window
        cv2.imshow("QR Detection in Real-Time", image_processed)

        if not TEST_VISION:
            sequence_queue = get_and_handle_message_for_robot_motion(client, 
                        robot_current_position, robot_current_forces, sequence_queue)
            # print("[QUEUE]", len(sequence_queue), sequence_queue)
            # print("[ROBOT POSITION]", robot_current_position)
            # print("[FORCES]", robot_current_forces)

            raw_qr_global_coords = robot_current_position.copy()  
            raw_qr_global_coords[0] = raw_qr_global_coords[0] - QR_POSITION[2] + raw_coord[2]
            raw_qr_global_coords[1] = raw_qr_global_coords[1] + QR_POSITION[0] - raw_coord[0]
            raw_qr_global_coords[2] = raw_qr_global_coords[2] + QR_POSITION[1] - raw_coord[1]

        if is_valid_code_detected:
            # Kalman measurement update
            mx, my, mz = raw_qr_global_coords[:3]
            measurement = np.array([[mx], [my], [mz]], np.float32)
            kalman.correct(measurement)

            # add data to history list
            if time.time() > start_time + WARM_UP_SKIP_TIME:
                history_robot_position.append(robot_current_position[:3])
                history_kalman_measurement.append([mx, my, mz])
                history_target_position.append([pred_x, pred_y, pred_z])
                history_kalman_prediction.append([pred_x, pred_y, pred_z])
                history_time.append(time.time() - start_time)

        # Kalman filter update
        prediction = kalman.predict()
        pred_x, pred_y, pred_z = int(prediction[0][0]), int(prediction[1][0]), int(prediction[2][0])

        # connection
        if time.time() > last_time_connection + CONNECTION_INTERVAL:
            last_time_connection = time.time()

            # send new command
            if not TEST_VISION and len(sequence_queue) < SEQUENCE_MAX_LENGTH:
                sequence_queue.append(sequence)
                sequence = move_robot_cartesian_representation_with_tcp_client(client, sequence, 
                                                x = pred_x if pred_x else robot_current_position[0],
                                                y = pred_y if pred_y else robot_current_position[1],
                                                z = pred_z if pred_z else robot_current_position[2],
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

    # draw graphs 2D
    plot_data(history_time, history_kalman_measurement, history_kalman_prediction,
                robot_label="measurement", target_label="prediction", 
                title="Kalman filter: measurement vs prediction",
                color_dict=COLOR_DICT_GREY_GREEN_RED)
    plot_data(history_time, history_robot_position, history_target_position,
                robot_label="robot", target_label="target", 
                title="Robot position vs target position",
                color_dict=COLOR_DICT_GREY_LIME_ORANGE)

    # draw graphs 3D
    plot_3d_trajectories([
        (history_kalman_measurement, "green", "Robot trajectory"),
        (history_kalman_prediction, "orange", "Target trajectory"),
    ])

if __name__ == "__main__":
    run()