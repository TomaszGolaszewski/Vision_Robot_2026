import socket
import threading
import time
import json
import copy
import random

#Tests
NUMBER_OF_MOVES = 100

# Connection
IP_ADDRESS = '192.168.11.101'
PORT_CONNECTION_PROCEDURE = 16001

# Robot
HOME_POSITION = {
	"j1": -50.5, 
	"j2": 25.0, 
	"j3": -40.0, 
	"j4": -118.0, 
	"j5": -61.0, 
	"j6": -13.0,
}

# Movement instruction templates
FRC_JOINT_REPRESENTATION_TEMPLATE_DICT = {
    # "Instruction": "FRC_JointMotionJRep",
    "Instruction": "FRC_JointRelativeJRep",
    "SequenceID": 0,
    "JointAngle": {
        "J1": 0,
        "J2": 0,
        "J3": 0,
        "J4": 0,
        "J5": 0,
        "J6": 0,
    },
    "SpeedType": "Percent",
    "Speed": 0,
    "TermType": "FINE", # FINE or CNT
    "TermValue": 0, # 1-100
}

FRC_CARTESIAN_REPRESENTATION_TEMPLATE_DICT = {
    # "Instruction": "FRC_JointMotion",
    "Instruction": "FRC_JointRelative",
    "SequenceID": 0,
    "Configuration": {
        "UToolNumber": 1,
        "UFrameNumber": 7,
        "Front": 1, 
        "Up": 1,
        "Left": 0, 
        "Flip": 0,
        "Turn4": 0,
        "Turn5": 0,
        "Turn6": 0,
    },
    "Position": {
        "X": 0, 
        "Y": 0, 
        "Z": 0,
        "W": 0, 
        "P": 0, 
        "R": 0,
    },
    "SpeedType": "Percent",
    "Speed": 0,
    "TermType": "FINE", # FINE or CNT
    "TermValue": 0, # 1-100
}

def decode_error_id(error_id: int) -> None:
    """Print information about the error received."""
    if error_id == 0:
        pass
    elif error_id == 7126:
        print("ERROR: 7126 - ??? robot is not mastered or its program buffer is full ???")
    elif error_id == 7015:
        print("ERROR: 7015 - ??? robot cannot move safely, you must select the program and move it manually to the home position ???")
    elif error_id == 458878:
        print("ERROR: 458878 - Program too long!")
    elif error_id == 2556936:
        print("ERROR: 2556936 - TP enabled!")
    elif error_id == 2556937:
        print("ERROR: 2556937 - ??? some errors on TP ???")
    elif error_id == 2556942:
        print("ERROR: 2556942 - ??? robot cannot move safely, you must select the program and move it manually to the home position ???")
    elif error_id == 2556943:
        print("ERROR: 2556943 - Last connection was not aborted!")
    elif error_id == 2556950:
        print("ERROR: 2556950 - >>> Wrong message structure!") 
    elif error_id == 2556952:
        print("ERROR: 2556952 - Program too long!")
    elif error_id == 2556955:
        print("ERROR: 2556955 - Messages are being sent too fast!")
    elif error_id == 2556956:
        print("ERROR: 2556956 - ??? motion aborted ???")
    elif error_id == 2556957:
        print("ERROR: 2556957 - Invalid SequenceID, length of path equals zero or RMI_MOVE program is open!")
    else:
        print(f"ERROR: {error_id} - NEW ERROR !!!")

# ===== CONNECTION =======================================================================

def rmi_send(sock: socket.socket, message: str, print_message: bool = True) -> None: 
    """Encode and send a message over an RMI socket."""
    if print_message:
        print("[SENDER]", message)
    sock.send(message.encode())

def rmi_read(sock: socket.socket, print_message: bool = True) -> dict: 
    """Receive and decode a JSON message from an RMI socket.
    Return: error_id nad message.
    """
    data = sock.recv(1024)
    # print(data)

    messages = [] 
    for line in data.splitlines(): 
        if line.strip(): 
            message = json.loads(line)

            error_id = message["ErrorID"]
            decode_error_id(error_id)
            
            messages.append(message) 
    
    if print_message:
        message_decoded = json.dumps(messages, indent=2)
        print(message_decoded)

    return error_id, message


def initialize_connection() -> socket.socket:
    """Create socket object, wait until all errors on robot are resolved and initialize the connection.
    Return connected socket object."""

    # get port to create connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.connect((IP_ADDRESS, PORT_CONNECTION_PROCEDURE))
        rmi_send(s1, '{"Communication": "FRC_Connect"}\r\n')
        error_id, msg = rmi_read(s1)

        if error_id == 0:
            print("Connected")

        # read port num  
        port_num = msg["PortNumber"]
    time.sleep(1)

    # create new socket
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.connect((IP_ADDRESS, port_num))
    time.sleep(1)

    # cancel old commands
    rmi_send(s2, '{"Command": "FRC_Abort"}\r\n')
    rmi_read(s2)
    time.sleep(0.5)

    # initialize connection
    error_id = 1
    while error_id:
        rmi_send(s2, '{"Command": "FRC_Initialize"}\r\n')
        error_id, msg = rmi_read(s2)
        if error_id == 0:
            print("Initialized")
            time.sleep(0.5)
        else:
            time.sleep(2)

    return s2

def close_connection(sock: socket.socket):
    """Cancel all commands, close the connection to the robot and close the socket."""

    # cancel all commands
    time.sleep(0.5)
    rmi_send(sock, '{"Command": "FRC_Abort"}\r\n')
    rmi_read(sock)

    # close the connection on robot side
    time.sleep(0.5)
    rmi_send(sock, '{"Communication": "FRC_Disconnect"}\r\n')
    rmi_read(sock)

    # close the connection on our side
    time.sleep(0.5)
    sock.close()

# ===== MOVEMENT =======================================================================

def prepare_command_move_robot_joint_representation(sequence: int, is_motion_relative: bool = False, 
                        j1: float = 0.0, j2: float = 0.0, j3: float = 0.0, 
                        j4: float = 0.0, j5: float = 0.0, j6: float = 0.0, 
                        speed: int = 100, accuracy: str = 'FINE') -> str:

    motion_dict = copy.deepcopy(FRC_JOINT_REPRESENTATION_TEMPLATE_DICT)

    motion_dict["Instruction"] = "FRC_JointRelativeJRep" if is_motion_relative else "FRC_JointMotionJRep"
    motion_dict["SequenceID"] = sequence
    motion_dict["JointAngle"]["J1"] = j1
    motion_dict["JointAngle"]["J2"] = j2
    motion_dict["JointAngle"]["J3"] = j3
    motion_dict["JointAngle"]["J4"] = j4
    motion_dict["JointAngle"]["J5"] = j5
    motion_dict["JointAngle"]["J6"] = j6
    motion_dict["Speed"] = speed
    motion_dict["TermType"] = "CNT" if accuracy == "CNT" else "FINE" # FINE or CNT
    motion_dict["TermValue"] = 100 if accuracy == "CNT" else 0 # 1-100

    return json.dumps(motion_dict, indent=2) + "\r\n"

def move_robot_joint_representation_with_socket(sock: socket.socket, sequence: int, is_motion_relative: bool = False, 
                        j1: float = 0.0, j2: float = 0.0, j3: float = 0.0, 
                        j4: float = 0.0, j5: float = 0.0, j6: float = 0.0, 
                        speed: int = 100, accuracy: str = 'FINE', wait_for_response: bool = True) -> int:

    motion_json = prepare_command_move_robot_joint_representation(
                        sequence=sequence, is_motion_relative=is_motion_relative,
                        j1=j1, j2=j2, j3=j3, j4=j4, j5=j5, j6=j6, speed=speed, accuracy=accuracy)

    rmi_send(sock, motion_json)
    if wait_for_response:
        rmi_read(sock)

    return sequence + 1

def prepare_command_move_robot_cartesian_representation(sequence: int, is_motion_relative: bool = False, 
                        x: float = 0.0, y: float = 0.0, z: float = 0.0, 
                        w: float = 0.0, p: float = 0.0, r: float = 0.0, 
                        speed: int = 100, accuracy: str = 'FINE') -> str:

    motion_dict = copy.deepcopy(FRC_CARTESIAN_REPRESENTATION_TEMPLATE_DICT)

    motion_dict["Instruction"] = "FRC_JointRelative" if is_motion_relative else "FRC_JointMotion"
    motion_dict["SequenceID"] = sequence
    motion_dict["Position"]["X"] = x
    motion_dict["Position"]["Y"] = y
    motion_dict["Position"]["Z"] = z
    motion_dict["Position"]["W"] = w
    motion_dict["Position"]["P"] = p
    motion_dict["Position"]["R"] = r
    motion_dict["Configuration"]["Front"] = 1
    motion_dict["Configuration"]["Up"] = 1
    motion_dict["Configuration"]["Left"] = 0
    motion_dict["Configuration"]["Flip"] = 0
    motion_dict["Configuration"]["Turn4"] = 0
    motion_dict["Configuration"]["Turn5"] = 0
    motion_dict["Configuration"]["Turn6"] = 0
    motion_dict["Speed"] = speed
    motion_dict["TermType"] = "CNT" if accuracy == "CNT" else "FINE" # FINE or CNT
    motion_dict["TermValue"] = 100 if accuracy == "CNT" else 0 # 1-100

    return json.dumps(motion_dict, indent=2) + "\r\n"

def move_robot_cartesian_representation_with_socket(sock: socket.socket, sequence: int, is_motion_relative: bool = False, 
                        x: float = 0.0, y: float = 0.0, z: float = 0.0, 
                        w: float = 0.0, p: float = 0.0, r: float = 0.0, 
                        speed: int = 100, accuracy: str = 'FINE', wait_for_response: bool = True) -> int:

    motion_json = prepare_command_move_robot_cartesian_representation(
                        sequence=sequence, is_motion_relative=is_motion_relative,
                        x=x, y=y, z=z, w=w, p=p, r=r, speed=speed, accuracy=accuracy)

    rmi_send(sock, motion_json)
    if wait_for_response:
        rmi_read(sock)

    return sequence + 1

def home_robot_with_socket(sock: socket.socket, sequence: int, speed: int = 100) -> int:
    """Move the robot to its HOME position."""
    rmi_send(sock, '{"Command" : "FRC_SetOverRide", "Value" : 10 } \r\n')
    rmi_read(sock)
    sequence = move_robot_joint_representation_with_socket(sock, sequence, **HOME_POSITION)
    time.sleep(1)
    rmi_send(sock, '{"Command" : "FRC_SetOverRide", "Value" : ' + str(speed) + ' } \r\n')
    rmi_read(sock)

    return sequence

# ===== TESTS =======================================================================

def test_robot_motion_interface():
    """Test of the prepared interface for connecting with the robot and its advanced functions."""

    sock = initialize_connection()
    sequence = 1 # ID of the motion command in RMI sequence

    # go to start position
    sequence = home_robot_with_socket(sock, sequence)

    for _ in range(NUMBER_OF_MOVES):
        print(sequence)
        r = random.randint(1, 3)
        sign = random.randint(0, 1)
        if not sign: sign = -1
        
        if r == 1:
            sequence = move_robot_cartesian_representation_with_socket(sock, sequence, is_motion_relative=True, x=sign*5.0)
        elif r == 2:
            sequence = move_robot_cartesian_representation_with_socket(sock, sequence, is_motion_relative=True, y=sign*5.0)
        else:
            sequence = move_robot_cartesian_representation_with_socket(sock, sequence, is_motion_relative=True, z=sign*5.0)
        time.sleep(0.2)

    close_connection(sock)

# ===== MAIN =======================================================================

if __name__ == "__main__":
    test_robot_motion_interface()