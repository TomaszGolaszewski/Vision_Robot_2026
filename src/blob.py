import numpy as np
import cv2
import time 
import math

from miscellaneous import get_objects_by_color, draw_points_from_list
from stabilization import handle_stabilized_points


AMPLIFICATION = 3000


def get_1D_color(x: int) -> list[int, int, int]:
    """Returns color from blue for 0 to red for 255 as RGB list."""
    x = int(x)
    if x < 0: 
        return (0, 0, 0)
    if x > 255: 
        return (255, 255, 255)
    
    red = x
    green = 0
    blue = 255 - x
    return [blue, green, red]

def field_value(list_with_blobs: list[tuple], x: int, y: int) -> int:
    """
    Calculates blobs field value based on distance from blob.

    Args:
        list_with_blobs (list): A list containing blob data to be used for determining
                                pixel values in format [(pos_x, pos_y)].
        x (int): x position of calculated point.
        y (int): y position of calculated point.

    Returns:
        int: blobs field value in indicated point.
    """
    value_sum = 0
    for blob in list_with_blobs:
        value_per_blob = math.sqrt((blob[0] - x) ** 2 + (blob[1] - y) ** 2)
        if value_per_blob < 1: 
            value_per_blob = 1
        value_sum += AMPLIFICATION / value_per_blob
    return int(value_sum)

def draw_blob(list_with_blobs: list, width: int, height: int) -> cv2.typing.MatLike:
    """
    Creates canva with blobs image.

    Args:
        list_with_blobs (list): A list containing blob data to be used for determining
                                pixel values in format [(pos_x, pos_y)].
        width (int): Width in pixels of created image. 
        height (int): height in pixels of created image. 

    Returns:
        MatLike: A 3D list representing the RGB image (height x width x color channels).
    """
    image = np.zeros((height, width, 3), dtype=np.uint8)
    for y, row in enumerate(image):
        for x, pixel in enumerate(row):
            value = field_value(list_with_blobs, x, y)
            pixel[:] = get_1D_color(value)

    return image

# ===== TESTS =================================================

def test_glowing_balls():

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
    # draw demo blobs
    # img = draw_blob([(10, 50), (20, 50), (300, 50), (370, 350)], 500, 500)
    # cv2.imshow("Blob", img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    test_glowing_balls()