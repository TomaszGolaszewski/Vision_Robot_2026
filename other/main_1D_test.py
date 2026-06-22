

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
from vision_QR import dist_two_points # calculate_object_position_3_dof
from draw_graph_2D import plot_data
from draw_graph_2D import COLOR_DICT_GREY_LIME_ORANGE, COLOR_DICT_GREY_GREEN_RED
from draw_graph_3D import plot_3d_trajectories



# -----------------------------------------------------------------

TEST_VISION = 0#True

CAMERA_ZERO = 80 # mm
ALLOWED_SPEED = 90 # %
CONNECTION_INTERVAL = 0.5 # s

TEST_POSITION = {
	"j1": -6.7, 
	"j2": 40.7, 
	"j3": -33.6, 
	"j4": -179.9, 
	"j5": 56.5, 
	"j6": -52.5,
}

# FRC_CARTESIAN_REPRESENTATION_TEMPLATE_DICT = {
#     "Instruction": "FRC_JointRelative",
#     "SequenceID": 0,
#     "Configuration": {
#         "UToolNumber": 1,
#         "UFrameNumber": 7,
#         "Front": 1, 
#         "Up": 1,
#         "Left": 0, 
#         "Flip": 1,
#         "Turn4": 0,
#         "Turn5": 0,
#         "Turn6": 0,
#     },
#     "Position": {
#         "X": 0, 
#         "Y": 0, 
#         "Z": 0,
#         "W": 0, 
#         "P": 0, 
#         "R": 0,
#     },
#     "SpeedType": "Percent",
#     "Speed": 0,
#     "TermType": "FINE", # FINE or CNT
#     "TermValue": 0, # 1-100
# }

# -----------------------------------------------------------------

def calculate_object_position_1_dof(vertices: list[list[float]]) -> list:
    # system calibration
    size_real = 50 # length in mm

    # calculate image size on screen
    size_image_x = dist_two_points(vertices[0], vertices[1])
    size_image_y = dist_two_points(vertices[0], vertices[3])
    size_image = max(size_image_x, size_image_y)

    # calculate image position in reality
    center_y = (vertices[0][1] + vertices[1][1] + vertices[2][1] + vertices[3][1]) / 4
    y = size_real * center_y / size_image
    # print("Raw camera pos y: ", y)
    return float(y), size_image

def reverse_object_position_1_dof(x, size_image):
    # system calibration
    size_real = 50 # length in mm
    return x * size_image / size_real

# -----------------------------------------------------------------

def run():

    # variables for time measurement
    i = 0
    start_time = time.time()
    last_time_fps = time.time()
    last_time_connection = time.time()# + WARM_UP_SKIP_TIME

    # robot variables
    robot_current_position = [0, 0, 0, 0, 0, 0]
    robot_current_forces = [0, 0, 0, 0, 0, 0]
    raw_y = 0
    size_image = 10
    sequence_queue = []
    sequence = 1 # ID of the motion command in RMI sequence
    last_target_position = 0

    # history
    history_time = []
    history_robot_position = []
    history_target_position = []
    history_kalman_measurement = []
    history_kalman_prediction = []

    # Kalman filter initialization
    kalman = cv2.KalmanFilter(2, 1)  # 2 dynamic params, 1 measurement params

    # state: [x, y, z, vx, vy, vz]
    # F - the state-transition model
    # A - macierz systemowa ukladu (macierz przejscia)
    kalman.transitionMatrix = np.array([
        [1, 1],
        [0, 1]
    ], dtype=np.float32)

    kalman.measurementMatrix = np.array([
        [1, 0]
    ], dtype=np.float32)

    # Q = niepewność modelu ruchu
    # Q - duże - ufamy pomiarom
    # Q = 0.03 # R = 0.5 error=40-50 ek=3.0
    Q = 0.1 # R = 0.5 error=40-45 ek=2.0
    # Q = 0.5 # R = 0.5 error=40-45
    kalman.processNoiseCov = np.eye(2, dtype=np.float32) * Q
    
    # R = niepewność pomiaru
    # R - duże ufamy modelowi, pomiary są zaszumione
    # R - malpomiary 
    # R = 0.5 # Q = 0.03 error=40-50
    # R = 0.1 # Q = 0.03 error=40-45
    R = 0.1 # Q = 0.1 error=50-60 ek=2.0
    # R = 0.1 # Q = 0.5 error=30-60 ek=1.8
    kalman.measurementNoiseCov = np.eye(1, dtype=np.float32) * R

    # measurement = np.zeros((3, 1), dtype=np.float32)
    prediction = np.zeros((1, 1), dtype=np.float32)

        # initializing webcam video capture
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Cannot open camera!")
        exit()

    if not TEST_VISION:
        client = initialize_connection_with_tcp_client()
        # go to start position
        send_message(client, '{"Command" : "FRC_SetOverRide", "Value" : 10 } \r\n')
        time.sleep(0.1)
        get_message(client)
        time.sleep(0.1)

        sequence = move_robot_joint_representation_with_tcp_client(client, sequence,
                                            **TEST_POSITION, wait_for_response=True)
        time.sleep(1)

        send_message(client, '{"Command" : "FRC_SetOverRide", "Value" : ' + str(ALLOWED_SPEED) + ' } \r\n')
        time.sleep(0.1)
        get_message(client)
        time.sleep(0.1)
    
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
                raw_y, size_image = calculate_object_position_1_dof(vertices_coords)
                
                # draw outlines of the codes
                image_processed = cv2.polylines(image_original_frame, [vertices_coords], True, (0, 255, 0), 3)

                # draw raw QR pos
                screen_y = reverse_object_position_1_dof(raw_y, size_image)
                cv2.line(image_processed, (90, int(screen_y)), (image_processed.shape[1]-100, int(screen_y)), (255, 0, 0), 3)

        if not TEST_VISION:
            # time.sleep(0.02)
            sequence_queue = get_and_handle_message_for_robot_motion(client, 
                        robot_current_position, robot_current_forces, sequence_queue)
            
        r_measurement_y = robot_current_position[1] + raw_y - CAMERA_ZERO
        # Kalman measurement update
        measurement = np.array([[r_measurement_y]], np.float32)
        kalman.correct(measurement)

        # Kalman filter update
        prediction = kalman.predict()
        r_prediction_y = prediction[0][0]
        v_prediction_y = prediction[1][0]
        # print(robot_current_position[1], r_measurement_y, r_prediction_y)
        # print("Error: ", robot_current_position[1] - r_prediction_y, "Err Kalm: ", r_measurement_y - r_prediction_y)

        # add data to history list
        if is_valid_code_detected and time.time() > start_time + WARM_UP_SKIP_TIME:
            history_robot_position.append(robot_current_position[1])
            history_kalman_measurement.append(r_measurement_y)
            history_target_position.append(r_prediction_y)
            history_kalman_prediction.append(r_prediction_y)
            history_time.append(time.time() - start_time)

        # draw predicted QR pos
        screen_y = reverse_object_position_1_dof(r_prediction_y + CAMERA_ZERO - robot_current_position[1], size_image) # PAMIETAC O DODANIU WEKTORA CAMERA ZERO !!!
        cv2.line(image_processed, (100, int(screen_y)), (image_processed.shape[1]-90, int(screen_y)), (0, 0, 255), 3)

        # connection
        if time.time() > last_time_connection + CONNECTION_INTERVAL \
                and time.time() > start_time + WARM_UP_SKIP_TIME:
            last_time_connection = time.time()

            # send new command
            if not TEST_VISION and len(sequence_queue) < SEQUENCE_MAX_LENGTH:# and distance_between_targets > 2:
                k=6
                # new_target = r_prediction_y + k * (r_prediction_y-last_target_position)
                new_target = r_prediction_y + k * v_prediction_y

                # draw pos
                screen_y = reverse_object_position_1_dof(new_target + CAMERA_ZERO - robot_current_position[1], size_image)
                cv2.line(image_processed, (110, int(screen_y)), (image_processed.shape[1]-110, int(screen_y)), (255, 255, 255), 3)

                last_target_position = r_prediction_y
                target = float(r_prediction_y)
                # target = float(new_target)
                
                sequence_queue.append(sequence)
                sequence = move_robot_cartesian_representation_with_tcp_client(client, sequence, 
                                                x = robot_current_position[0],
                                                y = target if target else robot_current_position[1],
                                                z = robot_current_position[2],
                                                w = robot_current_position[3],
                                                p = robot_current_position[4],
                                                r = robot_current_position[5],
                                                is_motion_relative=False)#, accuracy='CNT')

                print("[QUEUE]", len(sequence_queue), sequence_queue)

        # draw window
        cv2.imshow("QR Detection in Real-Time", image_processed)

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