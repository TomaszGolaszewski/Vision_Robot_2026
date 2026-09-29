# Global variables

# Connection
IP_ADDRESS = '192.168.11.101'
PORT_CONNECTION_PROCEDURE = 16001

# Vision
TEST_VISION = 0#True # True == test (vision only) or False == run with robot
SIMULATE_ROBOT_MOVEMENT = True
CAMERA_ID = 0 # 0
CONNECTION_INTERVAL = 0.2 # s

# QR code tracking variables
QR_TEXT = '001'
QR_POSITION = [140.0, 80.0, -440.0] # [x, y, z] mm
MAX_ALLOWED_OFFSET = 200 # 50 # mm
MIN_ALLOWED_OFFSET = 2 # mm

# Ultrasound therapy variables
CAMERA_CENTER_2_TCP = [0.0, -70.0] # [x, y] mm
TOOL_ANGLE_OFFSET = 120 # deg
BRIGHTNESS_THRESHOLD = 200
DPMM = 210 # dots (pixels) per 100 millimeters on camera image (fixed distance to camera)
MOVEMENT_ALONG_ARM_SPEED = 20 # mm/s
MOVEMENT_ALONG_ARM_INCREMENT = 20 # mm
SHOULDER_POSITION = [880, 200] # [900, 150] # [x, y] mm (global coordinates)
ARM_LENGTH = 400 # mm
ARM_WIDTH = 100 # mm
FLUCTUATION_PERIOD = 5 # s
MOTION_MODE = 1 # 1 = linear, 2 = sinusoidal

# Robot
UTOOLNUMBER = 1
UFRAMENUMBER = 7
ALLOWED_SPEED = 60 # %
REGISTER_NUMBER = 2
SEQUENCE_MAX_LENGTH = 7

X_MIN = 770 # mm
X_MAX = 1100
Y_MIN = -280
Y_MAX = 260 # 165
Z_ANGLE_MIN = 100 # 90 # deg
Z_ANGLE_MAX = 140 # 150

# TODO: add main HOME
# HOME_POSITION = {
# 	"j1": -50.5, 
# 	"j2": 25.0, 
# 	"j3": -40.0, 
# 	"j4": -118.0, 
# 	"j5": -61.0, 
# 	"j6": -13.0,
# }
HOME_POSITION_QR_TEST = {
	"j1": -50.5, 
	"j2": 25.0, 
	"j3": -40.0, 
	"j4": -118.0, 
	"j5": -61.0, 
	"j6": -13.0,
}
HOME_POSITION_1D_TEST = {
	"j1": -6.7, 
	"j2": 40.7, 
	"j3": -33.6, 
	"j4": -179.9, 
	"j5": 56.5, 
	"j6": -52.5,
}
# HOME_POSITION_HAND_TREATMENT_old_config = {
# 	"j1": -1, 
# 	"j2": 37.4, 
# 	"j3": -21.7, 
# 	"j4": -179.9, 
# 	"j5": 68.4, 
# 	"j6": -52.6,
# }
# HOME_POSITION_HAND_TREATMENT_old_position = {
# 	"j1": 18.5, 
# 	"j2": 33.5, 
# 	"j3": -25.5, 
# 	"j4": 1.3, 
# 	"j5": -63.8, 
# 	"j6": 102.0,
# }
HOME_POSITION_HAND_TREATMENT = {
	"j1": 24.8, 
	"j2": 34.7, 
	"j3": -24.4, 
	"j4": 1.1, 
	"j5": -65.5, 
	"j6": 95.0,
}

# Data settings
WARM_UP_SKIP_TIME = 4 # s
ROTATION_TIME = 4 # s

# UI variables
SHOW_KALMAN_ERROR = False # True
SHOW_ROBOT_ERROR = False # True
SHOW_3D_TRAJECTORIES = False

# Old debug variables
USE_FAKE_SOCKET = False