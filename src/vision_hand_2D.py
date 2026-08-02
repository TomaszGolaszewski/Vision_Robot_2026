import cv2
import numpy as np
import math

from settings import CAMERA_CENTER_2_TCP, DPMM


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


def calculate_real_hand_position(robot_position: list, 
                                 blob_center: list, 
                                 blob_eigenvector: list,
                                 img_height: int, 
                                 img_width: int) -> list:
    """Compute the real-world position of a detected object relative to the global 
                    robot coordinate system.

    Args:
        robot_position (list): coordinates of the robot's TCP.
        blob_center (list): pixel coordinates (x, y) of the detected object's center 
            in the camera image.
        blob_eigenvector (list): normalized 2D vector describing the
            orientation of the detected object.
        img_height (int): height of the camera image in pixels.
        img_width (int): width of the camera image in pixels.

    Returns:
        list: coordinates of the object in global coordinate frame.
    """
    camera_offset = np.array(CAMERA_CENTER_2_TCP)  # camera position relative to the robot's TCP (mm)
    mm_per_px = 100.0 / DPMM # DPMM = dots (pixels) per 100 millimeters on camera image

    # real position (mm) of the blob relative to the center of the image
    obj_x_on_camera = (blob_center[0] - img_width / 2) * mm_per_px
    obj_y_on_camera = (blob_center[1] - img_height / 2) * mm_per_px

    # global blob position
    obj_x = robot_position[0] + camera_offset[0] + obj_x_on_camera
    obj_y = robot_position[1] + camera_offset[1] + obj_y_on_camera
    obj_z = robot_position[2]

    # object orientation
    ex, ey = blob_eigenvector
    obj_angle = math.degrees(math.atan2(ey, ex))
    
    return [obj_x, obj_y, obj_z, obj_angle, robot_position[4], robot_position[5]]


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
        start_point (tuple[float, float]): initial (x, y) coordinates.
        angle_deg (float):
            Direction of the main trajectory in degrees.
            0° = +X axis, increasing counterclockwise.
        speed_mm_s (float): linear speed along the main direction (mm/s).
        time_s (float): time of motion (s).
        amplitude_mm (float): amplitude of the sinusoidal deviation (mm).
        period_s (float): length of one full sinusoidal period (s).

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


def draw_rotated_rectangle(panel, x_global, y_global, alpha_deg, color=(255, 0, 0)):
    """Draw rectangle symbolizing the found object."""

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

    # rotate and shift rectangle to the point in the screen coordinates
    point_on_screen = global_2_screen([x_global, y_global])
    rotated = (R @ corners.T).T
    rotated[:, 0] += point_on_screen[0] # x
    rotated[:, 1] += point_on_screen[1] # y

    # draw the rectangle on the panel
    pts = rotated.astype(np.int32)
    cv2.polylines(panel, [pts], isClosed=True, color=color, thickness=2)

    return panel

def draw_robot_position(image, x_global, y_global, alpha_deg, color=(0, 0, 255)):
    """Draw circle with line symbolizing the robot and its orientation."""
    radius = 20
    length = 30
    center_on_screen = global_2_screen([x_global, y_global])
    line_end = [
        int(center_on_screen[0] + length * math.cos(math.radians(alpha_deg))), 
        int(center_on_screen[1] + length * math.sin(math.radians(alpha_deg)))
    ]
    cv2.circle(image, center_on_screen, radius, color=color, thickness=2)
    cv2.line(image, center_on_screen, line_end, color=color, thickness=2)

def draw_trajectory(image, points_list, color=(255, 255, 255)):
    """Draw a trajectory on the given image by connecting consecutive points
    with straight line segments. 
    """
    for i, point_global in enumerate(points_list):
        if i > 0:
            point_screen = global_2_screen(point_global)
            previous_point_screen = global_2_screen(points_list[i - 1])
            cv2.line(image, point_screen, previous_point_screen, color, 1)

