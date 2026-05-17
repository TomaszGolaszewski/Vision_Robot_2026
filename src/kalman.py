import cv2
import numpy as np
import time

from miscellaneous import get_objects_by_color


def test_kalman_filter(ball_color="blue"):
    """
    """

    # lists with ball positions
    recorded_positions = []
    kalman_positions = []
    history_depth = 50

    # HSV color settings
    color_ranges = {
        "blue": [
            np.array([90, 80, 50], np.uint8),   
            np.array([130, 255, 255], np.uint8), 
        ],
        "green": [
            np.array([40, 70, 50], np.uint8),  
            np.array([80, 255, 255], np.uint8), 
        ],
        "green_dark": [
            np.array([70, 80, 50], np.uint8),  
            np.array([90, 200, 170], np.uint8), 
        ],
        "red": [
            np.array([136, 87, 111], np.uint8),   
            np.array([180, 255, 255], np.uint8), 
        ],
    }
    object_area_size = 1000 # size of the ball on the screen

    if ball_color not in color_ranges:
        print("Incorrect color! Please select: blue, green, red")
        return

    # capturing video through webcam
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Cannot open camera!")
        exit()

    # Kalman filter initialization
    kalman = cv2.KalmanFilter(4, 2)  # 4 dynamic params, 2 measurement params

    # state: [x, y, vx, vy]
    # F - the state-transition model
    # A – macierz systemowa układu (macierz przejścia)
    kalman.transitionMatrix = np.array([
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], np.float32)

    kalman.measurementMatrix = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0]
    ], np.float32)

    kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
    kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.5

    measurement = np.zeros((2, 1), np.float32)
    prediction = np.zeros((2, 1), np.float32)

    # preparing for time measurement
    last_time_frame = time.time()
    last_time_fps = time.time()
    frame_counter = 0
    delta_t = 0.1

    # start a while loop
    while True:

        if time.time() > last_time_frame + delta_t:
            last_time_frame = time.time()
            frame_counter += 1

            # reading the video from the webcam in image frames
            _, image_original_frame = webcam.read()
            # image_height, image_width, _ = image_original_frame.shape

            # detecting objects
            image_processed, coordinates_found = get_objects_by_color(
                                                    image_original_frame, 
                                                    area_threshold = object_area_size,
                                                    color_lower = color_ranges[ball_color][0],
                                                    color_upper = color_ranges[ball_color][1])

            # Kalman filter update
            prediction = kalman.predict()
            pred_x, pred_y = int(prediction[0][0]), int(prediction[1][0])

            if coordinates_found:
                # measurement update
                mx, my = coordinates_found[0]
                measurement = np.array([[mx], [my]], np.float32)
                kalman.correct(measurement)

                # draw ball position
                cv2.circle(image_original_frame, coordinates_found[0], 30, (255, 0, 0), 2)

                # add history
                recorded_positions.append(coordinates_found[0])
            kalman_positions.append((pred_x, pred_y))

            # trim history
            if len(recorded_positions) > history_depth:
                recorded_positions.pop(0)
            if len(kalman_positions) > history_depth:
                kalman_positions.pop(0)

            # draw recorded path
            for i in range(1, len(recorded_positions)):
                cv2.line(image_original_frame, recorded_positions[i - 1], recorded_positions[i], (0, 0, 255), 1)
                cv2.circle(image_original_frame, recorded_positions[i], 3, (0, 0, 255), -1)

            # draw kalman predicted path
            for i in range(3, len(kalman_positions)):
                if kalman_positions[i - 1] != (0, 0):
                    cv2.line(image_original_frame, kalman_positions[i - 1], kalman_positions[i], (0, 255, 0), 1)
                    cv2.circle(image_original_frame, kalman_positions[i], 3, (0, 255, 0), -1)

            # draw predicted point
            cv2.circle(image_original_frame, (pred_x, pred_y), 10, (0, 255, 0), 2)

            print("Detected:", coordinates_found, "Predicted:", (pred_x, pred_y))

            # concatenate images
            images_concatenated = np.concatenate((image_original_frame, image_processed), axis=1)

            # draw window
            cv2.imshow("Ball detection with Kalman filter", images_concatenated)

        # measure time
        if time.time() > last_time_fps + 1:
            last_time_fps = time.time()
            print("FPS:", frame_counter)
            frame_counter = 0

        # program termination
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    
    # clean up
    webcam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test_kalman_filter("green_dark")
