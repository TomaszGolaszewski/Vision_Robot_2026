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

        # decoded_text, vertices_coords, binarized_QR_code = qr_detect.detectAndDecode(image_original_frame)
        # is_code, vertices_coords = qr_detect.detect(image_original_frame)
        is_code, vertices_coords = qr_detect.detectMulti(image_original_frame)
        if is_code:
            for code_coords in vertices_coords:
                print(code_coords, end=" ")
            print("--------")


        # draw window
        cv2.imshow("QR Detection in Real-TIme", image_original_frame) #images_concatenated)

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