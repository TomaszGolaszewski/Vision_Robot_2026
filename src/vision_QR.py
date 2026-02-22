import numpy as np
import cv2
import time 
import math


def dist_two_points(point1, point2):
    """Calculate distance between two points."""
    # return math.sqrt((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2)
    return math.hypot(point1[0]-point2[0], point1[1]-point2[1])

def calculate_object_position_3_dof(vertices: list[list[float]]) -> list:
    """Calculate QR code position relative to the camera.
    Return Cartesian coordinates x, y, z.
    """
    # system calibration
    size_real = 50 # length in mm
    size_image_100 = 240 # length in pixels at a distance of 100 mm
    size_image_500 = 80 # length in pixels at a distance of 500 mm

    # calculate image size on screen
    size_image_x = dist_two_points(vertices[0], vertices[1])
    size_image_y = dist_two_points(vertices[0], vertices[3])
    # y = np.linalg.norm(vertices[0] - vertices[3])
    size_image = max(size_image_x, size_image_y)

    # calculate image position in reality
    z = (500 - 100) * (size_image - size_image_500) / (size_image_500 - size_image_100) + 500
    x = size_real * vertices[0][0] / size_image
    y = size_real * vertices[0][1] / size_image

    return [float(x), float(y), z]

# ===== TESTS =================================================

def test_vision_QR():

    # initializing QR code detector
    qr_detect = cv2.QRCodeDetector()

    # initializing webcam video capture
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Cannot open camera!")
        exit()

    # preparing for time measurement
    i = 0
    last_time = time.time()

    # start a while loop
    while(True):

        # reading the video from the webcam in image frames
        is_frame, image_original_frame = webcam.read()
        image_processed = image_original_frame.copy()

        # detect QR codes
        is_code, vertices_coords = qr_detect.detect(image_original_frame)
        # decoded_text, vertices_coords, binarized_straight_qrcode = qr_detect.detectAndDecode(image_original_frame)
        # is_code, vertices_coords = qr_detect.detectMulti(image_original_frame)
        # is_code, decoded_text, vertices_coords, binarized_straight_qrcode = qr_detect.detectAndDecodeMulti(image_original_frame)

        if is_code:
            x, y, z = calculate_object_position_3_dof(vertices_coords[0])
            print(x, y, z)

            # draw outlines of the codes
            image_processed = cv2.polylines(image_original_frame, vertices_coords.astype(int), True, (0, 255, 0), 3)

            # draw vertices numbers
            for i in range(4):
                image_processed = cv2.putText(image_processed, str(i), vertices_coords[0][i].astype(int), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

            # # draw code ids on the image
            # for text, points in zip(decoded_text, vertices_coords):
            #     image_processed = cv2.putText(image_processed, text, points[0].astype(int),
            #           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # draw window
        cv2.imshow("QR Detection in Real-TIme", image_processed) #image_original_frame) #images_concatenated)

           # measure time
        if time.time() > last_time + 1:
            last_time = time.time()
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
    test_vision_QR()