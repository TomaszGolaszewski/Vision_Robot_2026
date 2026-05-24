import numpy as np

def rotation_matrix_x(theta):
    return np.array([
        [1, 0, 0],
        [0, np.cos(theta), -np.sin(theta)],
        [0, np.sin(theta),  np.cos(theta)]
    ])

def rotation_matrix_y(theta):
    return np.array([
        [ np.cos(theta), 0, np.sin(theta)],
        [ 0,            1, 0],
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
