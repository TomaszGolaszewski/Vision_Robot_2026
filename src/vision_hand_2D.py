import cv2
import numpy as np
import math


# class Hand2D:
#     def __init__(self):
#         pass


def draw_axis(img, center, eigenvector, length=200, color=(255, 0, 0), thickness=2):
    """Function that draws the axis of symmetry using the PCA method.

    PCA (Principal Component Analysis - Analiza Składowych Głównych) 
    is a common statistical technique used for dimensionality reduction.
    (eigenvector - wektor własny)
    """
    x0, y0 = center
    x1 = int(x0 + eigenvector[0] * length)
    y1 = int(y0 + eigenvector[1] * length)
    x2 = int(x0 - eigenvector[0] * length)
    y2 = int(y0 - eigenvector[1] * length)

    cv2.line(img, (x1, y1), (x2, y2), color, thickness)


def detect_bright_blob(image_original: cv2.typing.MatLike, brightness_threshold: int = 150)-> tuple[cv2.typing.MatLike, list, list]:
    """
    Function detects objects from passed image and returns masked image and coordinates.

    Args:
        image_original (MatLike): Original image.
        brightness_threshold (int): The limit size of the area that defines the found object.

    Returns:
        MatLike: masked image with drawn objects.
        list: coordinates of center of the found object.
        list: coordinates of eigenvector of the found object.
    """

    gray = cv2.cvtColor(image_original, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # detect bright object
    _, thresh = cv2.threshold(blur, brightness_threshold, 255, cv2.THRESH_BINARY)

    # detect object outlines
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # the largest object
        largest = max(contours, key=cv2.contourArea)

        for cnt in contours:
            if cnt is largest:
                # red contour
                cv2.drawContours(image_original, [cnt], -1, (0, 0, 255), 3)

                # PCA for the symmetry axes
                # PCA (Principal Component Analysis - Analiza Składowych Głównych) 
                # is a common statistical technique used for dimensionality reduction.
                data = cnt.reshape(-1, 2).astype(np.float32)
                mean, eigenvectors, eigenvalues = cv2.PCACompute2(data, mean=None)
                # print(eigenvectors, np.linalg.norm(eigenvectors[0]))

                center = tuple(mean[0].astype(int))
                main_axis = eigenvectors[0]  # main axis

                # draw center
                cv2.circle(image_original, center, 5, color=(255, 0, 0), thickness=2)

                # draw the axis of symmetry (blue)
                draw_axis(image_original, center, main_axis, color=(255, 0, 0), thickness=2)

            else:
                # green contour
                cv2.drawContours(image_original, [cnt], -1, (0, 255, 0), 2)

    return image_original, center, main_axis


def calculate_real_position(robot_position: list, blob_center: list, blob_eigenvector: list) -> list:
    angle_rad = math.atan2(blob_eigenvector[1], blob_eigenvector[0])
    angle_deg = math.degrees(angle_rad)
    return *blob_center, angle_deg # np.pi/4


def create_side_panel(panel_height, panel_width):
    """Create black panel."""
    panel = np.zeros((panel_height, panel_width, 3), dtype=np.uint8)

def draw_rotated_rectangle(panel, x, y, alpha_deg, color=(255, 0, 0)):

    # rectangle size and orientation
    rect_width = 120
    rect_height = 80
    alpha = np.deg2rad(alpha_deg)

    # calculate rectangle corners
    dx = rect_width / 2
    dy = rect_height / 2
    corners = np.array([
        [-dx, -dy],
        [ dx, -dy],
        [ dx,  dy],
        [-dx,  dy]
    ])

    # rotation matrix
    R = np.array([
        [np.cos(alpha), -np.sin(alpha)],
        [np.sin(alpha),  np.cos(alpha)]
    ])

    # rotate and shift rectangle to the point (x, y)
    rotated = (R @ corners.T).T
    rotated[:, 0] += x
    rotated[:, 1] += y

    # draw the rectangle on the panel
    pts = rotated.astype(np.int32)
    cv2.polylines(panel, [pts], isClosed=True, color=color, thickness=2)

    return panel
