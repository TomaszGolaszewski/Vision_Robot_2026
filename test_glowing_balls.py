import numpy as np
import cv2
import time 

from src.miscellaneous import get_objects_by_color, draw_points_from_list
from src.blob import draw_blob
from src.stabilization import handle_stabilized_points


def run():

    canva_scale = 3
    object_area_size = 2000
    list_with_blob_objects = []

    # capturing video through webcam
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
        _, image_original_frame = webcam.read()
        image_height, image_width, _ = image_original_frame.shape

        # detecting objects
        image_processed, coordinates_found = get_objects_by_color(image_original_frame, object_area_size)

        # stabilization of objects coordinates
        list_with_blob_objects, stabilized_coordinates_found = handle_stabilized_points(list_with_blob_objects, coordinates_found)

        # scaling down, creatingcanva and scaling up - performance optimization
        objects_found_scaled = [(obj[0] // canva_scale, obj[1] // canva_scale) for obj in stabilized_coordinates_found]
        image_blob = draw_blob(objects_found_scaled, image_width // canva_scale, image_height // canva_scale)
        image_resized = cv2.resize(image_blob, (image_width, image_height), interpolation=cv2.INTER_LINEAR)

        # draw found coords on original image
        draw_points_from_list(image_original_frame, stabilized_coordinates_found, (0, 255, 255))

        # concatenate images
        images_concatenated = np.concatenate((image_original_frame, image_processed, image_resized), axis=1)
        # draw window
        cv2.imshow("Blob Detection in Real-TIme", images_concatenated)

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
    run()