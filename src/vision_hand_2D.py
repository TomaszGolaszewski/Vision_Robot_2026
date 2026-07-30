import cv2
import numpy as np
import math


# class Hand2D:
#     def __init__(self):
#         pass


# =========== DETECTION ===================================================================


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


# =========== MOTION ===================================================================


def trajectory_motion_linear(start_point, angle_deg, speed_mm_s, time_s):
    """
    Compute the new point position after moving from a start point
    in given direction (angle in degrees) with constant speed, over given time.

    Parameters:
        start_point (tuple[float, float]): the initial coordinates of the point
        angle_deg (float): movement direction in degrees
        speed_mm_s (float): speed in millimeters per second
        time_s (float): time of movement in seconds

    Returns:
        tuple[float, float]: new coordinates
    """

    angle_rad = math.radians(angle_deg)
    distance = speed_mm_s * time_s
    x = start_point[0] + distance * math.cos(angle_rad)
    y = start_point[1] + distance * math.sin(angle_rad)

    return x, y

import math

def trajectory_motion_sine(start_point, angle_deg, speed_mm_s, time_s,
                           amplitude_mm=50.0, period_s=5.0):
    """
    Compute the new 2D position of a point moving along a straight line while
    oscillating sinusoidally perpendicular to that line.

    The motion consists of:
    - linear displacement along the direction defined by angle_deg,
    - sinusoidal offset applied along the perpendicular direction.

    Parameters:
        start_point (tuple[float, float]):
            Initial (x, y) coordinates.

        angle_deg (float):
            Direction of the main trajectory in degrees.
            0° = +X axis, increasing counterclockwise.

        speed_mm_s (float):
            Linear speed along the main direction (mm/s).

        time_s (float):
            Time of motion (s).

        amplitude_mm (float):
            Amplitude of the sinusoidal deviation (mm).

        period_s (float):
            Length of one full sinusoidal period (s).

    Returns:
        tuple[float, float]:
            New (x, y) coordinates after applying linear and sinusoidal motion.
    """

    # convert angle to radians
    angle_rad = math.radians(angle_deg)

    # main direction vector
    dir_x = math.cos(angle_rad)
    dir_y = math.sin(angle_rad)

    # perpendicular direction vector (rotated +90°)
    perp_x = -math.sin(angle_rad)
    perp_y = math.cos(angle_rad)

    # linear displacement
    distance = speed_mm_s * time_s
    lin_x = start_point[0] + distance * dir_x
    lin_y = start_point[1] + distance * dir_y

    # angular frequency based on period
    omega = 2 * math.pi / period_s

    # sinusoidal offset
    offset = amplitude_mm * math.sin(omega * time_s)

    sin_x = offset * perp_x
    sin_y = offset * perp_y

    # final position
    return lin_x + sin_x, lin_y + sin_y


# =========== DRAWING ===================================================================


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


def global_2_screen(point: list) -> list:
    """Transform global coordinates to screen coordinates.
    
    X: 1100 - 770
    <---------------------  

    |
    | Y: -280
    |
    | Y: 165
    |
    V
    """
    x_left_edge = 1260
    y_top_edge = -280

    x = int(x_left_edge - point[0])
    y = int(point[1] - y_top_edge)

    return [x, y] #, *point[2:]]

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

def draw_robot_position(image, x_global, y_global, alpha_deg, color=(0, 0, 255)):
    radius = 20
    length = 30
    center = global_2_screen([x_global, y_global])
    line_end = [
        int(center[0] + length * math.cos(math.radians(alpha_deg))), 
        int(center[1] + length * math.sin(math.radians(alpha_deg)))
    ]
    cv2.circle(image, center, radius, color=color, thickness=2)
    cv2.line(image, center, line_end, color=color, thickness=2)

def draw_trajectory(image, points_list, color=(255, 255, 255)):
    """Draw a trajectory on the given image by connecting consecutive points
    with straight line segments. 
    """
    for i, point_global in enumerate(points_list):
        if i > 0:
            point_screen = global_2_screen(point_global)
            previous_point_screen = global_2_screen(points_list[i - 1])
            cv2.line(image, point_screen, previous_point_screen, color, 1)

