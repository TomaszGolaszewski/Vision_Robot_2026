import math
import numpy as np

def rotation_matrix_2d(theta):
    return np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta), np.cos(theta)]
    ])

def rotation_matrix_x(theta):
    return np.array([
        [1, 0, 0],
        [0, np.cos(theta), -np.sin(theta)],
        [0, np.sin(theta),  np.cos(theta)]
    ])

def rotation_matrix_y(theta):
    return np.array([
        [ np.cos(theta), 0, np.sin(theta)],
        [ 0,             1, 0            ],
        [-np.sin(theta), 0, np.cos(theta)]
    ])

def rotation_matrix_z(theta):
    return np.array([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta),  np.cos(theta), 0],
        [0,              0,             1]
    ])

def rotation_matrix_yaw_pitch_roll(yaw, pitch, roll):
    Rz = rotation_matrix_z(yaw)
    Ry = rotation_matrix_y(pitch)
    Rx = rotation_matrix_x(roll)
    return Rz @ Ry @ Rx


def clamp(value: float, minimum: float, maximum: float) -> float:
    """
    Restrict a value to a specified range.

    Args:
        value: The value to be constrained.
        minimum: The lower bound of the range.
        maximum: The upper bound of the range.

    Returns:
        The original value if it is within the range
        [minimum, maximum]. Otherwise, returns the
        nearest boundary value.

    Raises:
        ValueError: If minimum is greater than maximum.
    """
    if minimum > maximum:
        raise ValueError("minimum cannot be greater than maximum")

    return max(minimum, min(value, maximum))


def dist_two_points(point1, point2):
    """Calculate distance between two points."""
    # return math.sqrt((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2)
    return math.hypot(point1[0]-point2[0], point1[1]-point2[1])