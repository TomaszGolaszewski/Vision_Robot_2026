# Global variables

# Connection
IP_ADDRESS = '192.168.11.101'
PORT_CONNECTION_PROCEDURE = 16001

# Vision
TEST_VISION = 1 # True == test (vision only) or False == run with robot
CONNECTION_INTERVAL = 0.3 # s
QR_TEXT = '001'
QR_POSITION = [140.0, 80.0, 440.0] # [x, y, z] mm
MAX_ALLOWED_OFFSET = 200 # 50 # mm
MIN_ALLOWED_OFFSET = 2 # mm
ALLOWED_SPEED = 60 # %

# Robot
REGISTER_NUMBER = 1
SEQUENCE_MAX_LENGTH = 7
HOME_POSITION = {
	"j1": -50.5, 
	"j2": 25.0, 
	"j3": -40.0, 
	"j4": -118.0, 
	"j5": -61.0, 
	"j6": -13.0,
}

# Old debug variables
USE_FAKE_SOCKET = False # True