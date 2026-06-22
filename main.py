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
from functions_math import *
from robot_motion_interface import *
from robot_motion_tcp_client import *
from stabilization import handle_stabilized_points
from vision_QR import calculate_object_position_3_dof
from draw_graph_2D import plot_data
from draw_graph_2D import COLOR_DICT_GREY_LIME_ORANGE, COLOR_DICT_GREY_GREEN_RED
from draw_graph_3D import plot_3d_trajectories
from pid import *

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
    last_target_position = np.array([0, 0, 0], dtype=np.float32)

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
    ], dtype=np.float32)

    kalman.measurementMatrix = np.array([
        [1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0]
    ], dtype=np.float32)

    kalman.processNoiseCov = np.eye(6, dtype=np.float32) * 0.03
    kalman.measurementNoiseCov = np.eye(3, dtype=np.float32) * 0.5

    # measurement = np.zeros((3, 1), dtype=np.float32)
    prediction = np.zeros((3, 1), dtype=np.float32)

    # PID
    # pid = PID3D(Kp=[1.2, 1.2, 1.2],
    #             Ki=[0.1, 0.1, 0.1],
    #             Kd=[0.05, 0.05, 0.05])
    
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
    # frame_id = 0

    # start a while loop
    while True:

        if not TEST_VISION:
            request_status(client)

        # reading the video from the webcam in image frames
        is_frame, image_original_frame = webcam.read()
        image_processed = image_original_frame.copy()
  
        # detect QR codes using pyzbar
        decoded_objects = decode(image_original_frame)

        is_valid_code_detected = False
        for obj in decoded_objects:
            if obj.data.decode()[:3] == QR_TEXT:
                is_valid_code_detected = True

                # calculate the coordinates of the QR code relative to the camera
                vertices_coords = np.array([[p.x, p.y] for p in obj.polygon], dtype=np.int32)
                raw_coord = calculate_object_position_3_dof(vertices_coords)

                s_qr_2_camera = np.array(raw_coord, dtype=np.float32)

                # draw outlines of the codes
                image_processed = cv2.polylines(image_original_frame, [vertices_coords], True, (0, 255, 0), 3)

                # save frame image
                # cv2.imwrite(os.path.join("klatki", f"frame{frame_id:06d}.jpg"), image_processed) # image_original_frame)
                # frame_id += 1

        # draw window
        cv2.imshow("QR Detection in Real-Time", image_processed)

        if not TEST_VISION:
            # time.sleep(0.02)
            sequence_queue = get_and_handle_message_for_robot_motion(client, 
                        robot_current_position, robot_current_forces, sequence_queue)
            # print("[QUEUE]", len(sequence_queue), sequence_queue)
            # print("[ROBOT POSITION]", robot_current_position)
            # print("[FORCES]", robot_current_forces)
            r_tcp = np.array(robot_current_position[:3], dtype=np.float32)

        # if is_valid_code_detected:
        r_measurement = r_tcp + R_camera_2_tcp @ (s_target_2_qr - s_qr_2_camera)
        
        # Kalman measurement update
        kalman.correct(r_measurement.reshape(-1, 1).astype(np.float32))

        # Kalman filter update
        prediction = kalman.predict()
        r_prediction = prediction.reshape(-1)[:3]
        v_prediction = prediction.reshape(-1)[3:]

        # add data to history list
        if is_valid_code_detected and time.time() > start_time + WARM_UP_SKIP_TIME:
            history_robot_position.append(robot_current_position[:3])
            history_kalman_measurement.append(r_measurement)
            history_target_position.append(r_prediction)
            history_kalman_prediction.append(r_prediction)
            history_time.append(time.time() - start_time)

        # connection
        if time.time() > last_time_connection + CONNECTION_INTERVAL \
                and time.time() > start_time + WARM_UP_SKIP_TIME:
            last_time_connection = time.time()
            distance_between_targets = np.linalg.norm(last_target_position - r_prediction)
            s_error = last_target_position - r_prediction
            print("Distance between targets: ", distance_between_targets)
            last_target_position = np.array(r_prediction)

            # send new command
            if not TEST_VISION and len(sequence_queue) < SEQUENCE_MAX_LENGTH:# and distance_between_targets > 2:

                # prediction test
                # k=2
                # r_prediction = r_prediction + k * v_prediction

                # PID test
                # s_control = pid.update(robot_current_position[:3], r_prediction)
                # r_prediction = robot_current_position[:3] + s_control

                sequence_queue.append(sequence)
                sequence = move_robot_cartesian_representation_with_tcp_client(client, sequence, 
                                                x = r_prediction[0].item() if r_prediction[0] else robot_current_position[0],
                                                y = r_prediction[1].item() if r_prediction[1] else robot_current_position[1],
                                                z = r_prediction[2].item() if r_prediction[2] else robot_current_position[2],
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