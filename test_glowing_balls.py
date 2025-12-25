import numpy as np
import cv2
import time 

from src.miscellaneous import get_objects_by_color


def run():

    # capturing video through webcam
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Cannot open camera!")
        exit()

    # prepare for time measurement
    i = 0
    last_time = time.time()

    # start a while loop
    while(True):

        # reading the video from the webcam in image frames
        _, image_original_frame = webcam.read()

        image_processed, objects_found = get_objects_by_color(image_original_frame)

        # concatenate images
        # row1 = np.concatenate((red_mask, red_mask_2), axis=1)
        # row1_color = cv2.cvtColor(row1, cv2.COLOR_GRAY2BGR) # convert array from 1 to 3 channels
        # row2 = np.concatenate((res_red, imageFrame), axis=1)
        # allImages = np.concatenate((row1_color, row2), axis=0)
        images_concatenated = np.concatenate((image_original_frame, image_processed), axis=1)
        # draw window
        cv2.imshow("Red Color Detection in Real-TIme", images_concatenated)
        # cv2.imshow("Red Color Detection in Real-TIme", allImages)

        # measure time
        if time.time() > last_time + 1:
            last_time = time.time()
            print("FPS:" + str(i))
            i = 0
        else:
            i+=1

        # program termination
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    
    # clean up
    webcam.release()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    run()