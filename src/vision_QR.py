import numpy as np
import cv2
import time 


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
        # decoded_text, vertices_coords, binarized_straight_qrcode = qr_detect.detectAndDecode(image_original_frame)
        # is_code, vertices_coords = qr_detect.detect(image_original_frame)
        # is_code, vertices_coords = qr_detect.detectMulti(image_original_frame)
        is_code, decoded_text, vertices_coords, binarized_straight_qrcode = qr_detect.detectAndDecodeMulti(image_original_frame)

        if is_code:
            print(vertices_coords)
            print("--------")

            # draw outlines of the codes
            image_processed = cv2.polylines(image_original_frame, vertices_coords.astype(int), True, (0, 255, 0), 3)

            # draw code ids on the image
            for text, points in zip(decoded_text, vertices_coords):
                image_processed = cv2.putText(image_processed, text, points[0].astype(int),
                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

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