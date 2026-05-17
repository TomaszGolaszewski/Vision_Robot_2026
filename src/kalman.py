import cv2
import numpy as np
import time

from miscellaneous import get_objects_by_color


def test_kalman_filter(ball_color="blue"):
    """
    """

    # lists with ball positions
    recorded_positions = []

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

    # preparing for time measurement
    last_time = time.time()
    delta_t = 0.1

    # start a while loop
    while(True):

        # measure time
        if time.time() > last_time + delta_t:
            last_time = time.time()

            # reading the video from the webcam in image frames
            _, image_original_frame = webcam.read()
            image_height, image_width, _ = image_original_frame.shape

            # detecting objects
            image_processed, coordinates_found = get_objects_by_color(image_original_frame, 
                                    area_threshold = object_area_size,
                                    color_lower = color_ranges[ball_color][0],
                                    color_upper = color_ranges[ball_color][1])

            if coordinates_found:
                recorded_positions.append(coordinates_found[0])
                # draw ball position
                cv2.circle(image_original_frame, coordinates_found[0], 30, (255, 0, 0), 2)

            # draw path of recorded ball position
            for i in range(1, len(recorded_positions)):
                cv2.line(image_original_frame, recorded_positions[i - 1], recorded_positions[i], (0, 0, 255), 2)

            print(coordinates_found, len(recorded_positions))

            # concatenate images
            images_concatenated = np.concatenate((image_original_frame, image_processed), axis=1)

            # draw window
            cv2.imshow("Ball detection in real-time", images_concatenated)

        # program termination
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    
    # clean up
    webcam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test_kalman_filter("green_dark")
