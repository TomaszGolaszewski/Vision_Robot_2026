import numpy as np
import cv2
import os
import math


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


if __name__ == "__main__":
    # draw demo blobs
    img = draw_blob([(10, 50), (20, 50), (300, 50), (370, 350)])
    cv2.imshow("Blob", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()