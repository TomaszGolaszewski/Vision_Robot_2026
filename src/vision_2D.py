import numpy as np
import cv2
import time 

from miscellaneous import get_objects_by_color
from stabilization import handle_stabilized_points


def get_object_coord(webcam) -> tuple:

    object_area_size = 2000

    # reading the video from the webcam in image frames
    _, image_original_frame = webcam.read()
    image_height, image_width, _ = image_original_frame.shape

    # detecting objects
    image_processed, coordinates_found = get_objects_by_color(image_original_frame, object_area_size)

    # concatenate images
    images_concatenated = np.concatenate((image_original_frame, image_processed), axis=1)
    # draw window
    cv2.imshow("Blob Detection in Real-TIme", images_concatenated)
    
    return coordinates_found

# ===== TESTS =================================================

def test_vision_2D():

    # coords
    object_coord = (0, 0)
    object_last_coord = (0, 0)
    object_delta_coord = (0, 0)
    object_stabilized_coord = (0, 0)
    object_stabilized_last_coord = (0, 0)
    object_stabilized_delta_coord = (0, 0)
    list_with_objects = []

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

        object_coords = get_object_coord(webcam)
        # stabilization of objects coordinates
        list_with_objects, object_stabilized_coords = handle_stabilized_points(
                                            list_with_objects, object_coords.copy())   
        flag_stab = "s"    
        if object_stabilized_coords:
            flag_stab = "new_stab" 
            object_stabilized_last_coord = object_stabilized_coord
            object_stabilized_coord = object_stabilized_coords[0]
            object_stabilized_delta_coord = \
                [int(c - lc) for c, lc in zip(object_stabilized_coord, object_stabilized_last_coord)]

        flag_org = "o"
        if object_coords:
            flag_org = "new_org"
            object_last_coord = object_coord
            object_coord = object_coords[0]
            object_delta_coord = [c - lc for c, lc in zip(object_coord, object_last_coord)]
        print(flag_org, object_coord, object_delta_coord, "|", 
                    flag_stab, object_stabilized_coord, object_stabilized_delta_coord)

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
    test_vision_2D()