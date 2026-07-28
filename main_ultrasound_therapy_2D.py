# Vision Robot 2026
# By Tomasz Golaszewski
# 12.2025 -

# R - macierz obrotu / rotation matrix
# r - wektor wodzacy / global vector
# s - wektor lokalny / local vector

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
from functions_math import *
from robot_motion_interface import *
from robot_motion_tcp_client import *
from vision_hand_2D import detect_bright_blob, calculate_real_position, draw_rotated_rectangle
from draw_graph_2D import plot_data
from draw_graph_2D import COLOR_DICT_GREY_LIME_ORANGE, COLOR_DICT_GREY_GREEN_RED
from draw_graph_3D import plot_3d_trajectories
from pid import *

def run():

    # variables for time measurement
    i = 0
    start_time = time.time()
    last_time_fps = time.time()
    last_time_connection = time.time()

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

    # vectors
    s_qr_2_camera = np.array([0, 0, 0], dtype=np.float32) # position of the QR code relative to the camera
    s_target_2_qr = np.array(QR_POSITION, dtype=np.float32) # position of target point relative to the QR code 
    r_tcp = np.array(robot_current_position[:3], dtype=np.float32) # global position of robot tcp
    # temporary fixed camera position relative to tcp
    R_camera_2_tcp = rotation_matrix_x(np.pi / 2) @ rotation_matrix_y(np.pi / 2) 

    # Kalman filter initialization
    kalman = cv2.KalmanFilter(4, 2)  # 6 dynamic params, 3 measurement params

    # state: [x, alpha, vx, omega (v_alpha)]
    # F - the state-transition model
    # A - macierz systemowa ukladu (macierz przejscia)
    kalman.transitionMatrix = np.array([
        [1, 0, 0, 1],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], dtype=np.float32)

    kalman.measurementMatrix = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0]
    ], dtype=np.float32)

    kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
    kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.5

    # measurement = np.zeros((2, 1), dtype=np.float32)
    prediction = np.zeros((2, 1), dtype=np.float32)
    
    # initializing webcam video capture
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Cannot open camera!")
        exit()

    if not TEST_VISION:
        client = initialize_connection_with_tcp_client()
        # go to start position
        sequence = home_robot_with_tcp_client(client, sequence, 
                                            home_pos=HOME_POSITION_HAND_TREATMENT, speed=ALLOWED_SPEED)
    
    # restart time
    start_time = time.time()
    # frame_id = 0

    # start a while loop
    while True:

        if not TEST_VISION:
            request_status(client)

        # reading the video from the webcam in image frames
        is_frame, image_original_frame = webcam.read()
        image_processed = image_original_frame.copy()
        image_height, image_width = image_original_frame.shape[:2]
    
        # TODO: detect hand

        # detect hand position as the lightest blob
        image_processed, blob_center, blob_main_axis = detect_bright_blob(image_processed)

        if not TEST_VISION:
            # time.sleep(0.02)
            sequence_queue = get_and_handle_message_for_robot_motion(client, 
                        robot_current_position, robot_current_forces, sequence_queue)
            # print("[QUEUE]", len(sequence_queue), sequence_queue)
            # print("[ROBOT POSITION]", robot_current_position)
            # print("[FORCES]", robot_current_forces)
            r_tcp = np.array(robot_current_position[:3], dtype=np.float32)

        # if is_valid_code_detected:
        # r_measurement = r_tcp + R_camera_2_tcp @ (s_target_2_qr - s_qr_2_camera)
        # TODO:
        x, y, alpha = calculate_real_position(robot_current_position, blob_center, blob_main_axis)

        side_panel = np.zeros((image_height, image_width, 3), dtype=np.uint8)
        draw_rotated_rectangle(side_panel, x, y, alpha, color=(255, 0, 0))

        # concatenate images and draw window
        images_concatenated = np.concatenate((image_processed, side_panel), axis=1)
        cv2.imshow("QR Detection in Real-Time", images_concatenated)

        # TODO:
        # Kalman measurement update
        # kalman.correct(r_measurement.reshape(-1, 1).astype(np.float32))

        # Kalman filter update
        # prediction = kalman.predict()
        # r_prediction = prediction.reshape(-1)[:3]

        # TODO:
        # # add data to history list
        # if is_valid_code_detected and time.time() > start_time + WARM_UP_SKIP_TIME:
        #     history_robot_position.append(robot_current_position[:3])
        #     history_kalman_measurement.append(r_measurement)
        #     history_target_position.append(r_prediction)
        #     history_kalman_prediction.append(r_prediction)
        #     history_time.append(time.time() - start_time)

        # connection
        if time.time() > last_time_connection + CONNECTION_INTERVAL \
                and time.time() > start_time + WARM_UP_SKIP_TIME:
            last_time_connection = time.time()

            # send new command
            if not TEST_VISION and len(sequence_queue) < SEQUENCE_MAX_LENGTH:

                sequence_queue.append(sequence)
                # TODO:
                # sequence = move_robot_cartesian_representation_with_tcp_client(client, sequence, 
                #                                 x = r_prediction[0].item() if r_prediction[0] else robot_current_position[0],
                #                                 y = r_prediction[1].item() if r_prediction[1] else robot_current_position[1],
                #                                 z = r_prediction[2].item() if r_prediction[2] else robot_current_position[2],
                #                                 w = robot_current_position[3],
                #                                 p = robot_current_position[4],
                #                                 r = robot_current_position[5],
                #                                 is_motion_relative=False, accuracy='CNT')

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
    if SHOW_KALMAN_ERROR:
        plot_data(history_time, history_kalman_measurement, history_kalman_prediction,
                        robot_label="measurement", target_label="prediction", 
                        title="Kalman filter: measurement vs prediction",
                        color_dict=COLOR_DICT_GREY_GREEN_RED)
    if SHOW_ROBOT_ERROR:
        plot_data(history_time, history_robot_position, history_target_position,
                        robot_label="robot", target_label="target", 
                        title="Robot position vs target position",
                        color_dict=COLOR_DICT_GREY_LIME_ORANGE)

    # draw graphs 3D
    if SHOW_3D_TRAJECTORIES:
        plot_3d_trajectories([
                        (history_kalman_measurement, "green", "Robot trajectory"),
                        (history_kalman_prediction, "orange", "Target trajectory"),
                        ([[0,0,0], robot_current_position[:3]], "black", "Robot")])

if __name__ == "__main__":
    run()