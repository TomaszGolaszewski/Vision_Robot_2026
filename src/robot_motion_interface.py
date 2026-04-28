import socket
import threading
import time
import json
import copy
import random

from settings import *
from fake_socket import *


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

RMI_ERRORID_REFERENCE_TABLE = {
    2556929: "RMIT-001 Internal System Error.",
    2556930: "RMIT-002 Invalid UTool Number.",
    2556931: "RMIT-003 Invalid UFrame Number.",
    2556932: "RMIT-004 Invalid Position Register.",
    2556933: "RMIT-005 Invalid Speed Override.",
    2556934: "RMIT-006 Cannot Execute TP program.",
    2556935: "RMIT-007 Controller Servo is Off.",
    2556936: "RMIT-008 Teach Pendant is Enabled.",
    2556937: "RMIT-009 RMI is Not Running.",
    2556938: "RMIT-010 TP Program is Not Paused.",
    2556939: "RMIT-011 Cannot Resume TP Program.",
    2556940: "RMIT-012 Cannot Reset Controller.",
    2556941: "RMIT-013 Invalid RMI Command.",
    2556942: "RMIT-014 RMI Command Fail.",
    2556943: "RMIT-015 Invalid Controller State.",
    2556944: "RMIT-016 Please Cycle Power.",
    2556945: "RMIT-017 Invalid Payload Schedule.",
    2556946: "RMIT-018 Invalid Motion Option.",
    2556947: "RMIT-019 Invalid Vision Register.",
    2556948: "RMIT-020 Invalid RMI Instruction.",
    2556949: "RMIT-021 Invalid Value.",
    2556950: "RMIT-022 Invalid Text String",
    2556951: "RMIT-023 Invalid Position Data",
    2556952: "RMIT-024 RMI is In HOLD State",
    2556953: "RMIT-025 Remote Device Disconnected.",
    2556954: "RMIT-026 Robot is Already Connected.",
    2556955: "RMIT-027 Wait for Command Done.",
    2556956: "RMIT-028 Wait for Instruction Done.",
    2556957: "RMIT-029 Invalid sequence ID number.",
    2556958: "RMIT-030 Invalid Speed Type.",
    2556959: "RMIT-031 Invalid Speed Value.",
    2556960: "RMIT-032 Invalid Term Type.",
    2556961: "RMIT-033 Invalid Term Value.",
    2556962: "RMIT-034 Invalid LCB Port Type.",
    2556963: "RMIT-035 Invalid ACC Value.",
    2556964: "RMIT-036 Invalid Destination Position",
    2556965: "RMIT-037 Invalid VIA Position.",
    2556966: "RMIT-038 Invalid Port Number.",
    2556967: "RMIT-039 Invalid Group Number",
    2556968: "RMIT-040 Invalid Group Mask",
    2556969: "RMIT-041 Joint motion with COORD",
    2556970: "RMIT-042 Incremental motn with COORD",
    2556971: "RMIT-043 Robot in Single Step Mode",
    2556972: "RMIT-044 Invalid Position Data Type",
    2556973: "RMIT-045 Not Ready for ASCII Packet",
    2556974: "RMIT-046 ASCII Conversion Failed",
    2556975: "RMIT-047 Invalid ASCII Instruction",
    2556976: "RMIT-048 Invalid Number of Groups",
    2556977: "RMIT-049 Invalid Instruction packet",
    2556978: "RMIT-050 Invalid ASCII packet",
    2556979: "RMIT-051 Invalid ASCII string size",
    2556980: "RMIT-052 Invalid Application Tool",
    2556981: "RMIT-053 Invalid Call Program Name",
    2556982: "RMIT-054 Joint Motion with ALIM",
    2256983: "RMIT-055 ALIM option is not loaded",
    2256984: "RMIT-056 Need to finish S-motion",
    2256985: "RMIT-057 Spline option is not loaded",
    7004: "MEMO-004 Specific program is in use",
    7015: "MEMO-015 Program already exists",
}

def decode_error_id(error_id: int) -> None:
    """Print information about the error received."""
    if error_id == 0:
        pass
    elif error_id == 7126:
        print("[ERROR: 7126] ??? robot is not mastered or its program buffer is full or memory full???")
    elif error_id == 458878:
        print("[ERROR: 458878] ??? Program too long or memory full ???")
    elif error_id in RMI_ERRORID_REFERENCE_TABLE:
        print(f"[ERROR: {error_id}] {RMI_ERRORID_REFERENCE_TABLE[error_id]}")
        if error_id == 2556942:
            print("[ERROR: 2556942] ??? robot cannot move safely, you must select the program and move it manually to the home position ???")
        elif error_id == 2556943:
            print("[ERROR: 2556943] Last connection was not aborted!")
    else:
        print(f"[ERROR: {error_id}] NEW ERROR !!!")

# ===== CONNECTION =======================================================================

def rmi_send(sock: socket.socket, message: str, print_message: bool = False) -> None: 
    """Encode and send a message over an RMI socket."""
    if print_message:
        print("[SENDER]", message)
    sock.send(message.encode())

def rmi_read(sock: socket.socket, print_message: bool = False) -> dict: 
    """Receive and decode a JSON message from an RMI socket.
    Return: error_id nad message.
    """
    data = sock.recv(1024)

    messages = [] 
    for line in data.splitlines(): 
        if line.strip(): 
            message = json.loads(line)

            error_id = message["ErrorID"]
            if error_id:
                print(json.dumps(message, indent=2))
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

def print_robot_position():
    """Connect to the robot and read its current joint and Cartesian position."""
    sock = initialize_connection()
    time.sleep(0.5)
    rmi_send(sock, '{"Command": "FRC_ReadJointAngles"}\r\n')
    rmi_read(sock)
    time.sleep(0.5)
    rmi_send(sock, '{"Command": "FRC_ReadCartesianPosition"}\r\n')
    rmi_read(sock)
    time.sleep(0.5)
    close_connection(sock)

def move_robot_to_home_position():
    """Connect with robot and move it to its HOME position."""
    sock = initialize_connection()
    home_robot_with_socket(sock, 1, ALLOWED_SPEED)
    close_connection(sock)

def test_robot_motion_interface():
    """Test of the prepared interface for connecting with the robot and its advanced functions."""
    if USE_FAKE_SOCKET:
        # use simulated socket - local debug mode
        sock = FakeSocket()
    else:
        sock = initialize_connection()
    sequence = 1 # ID of the motion command in RMI sequence

    # go to start position
    sequence = home_robot_with_socket(sock, sequence)

    for _ in range(100):
        r = random.randint(1, 3)
        sign = random.randint(0, 1)
        if not sign: sign = -1
        
        if r == 1:
            sequence = move_robot_cartesian_representation_with_socket(sock, sequence, is_motion_relative=True, x=sign*5.0)
        elif r == 2:
            sequence = move_robot_cartesian_representation_with_socket(sock, sequence, is_motion_relative=True, y=sign*5.0)
        else:
            sequence = move_robot_cartesian_representation_with_socket(sock, sequence, is_motion_relative=True, z=sign*5.0)

    # time.sleep(0.5)
    # rmi_send(sock, '{"Command" : "FRC_GetStatus"} \r\n')
    # rmi_read(sock)
    # "TPMode": 0, - ok, "TPMode": 1, enabled

    # time.sleep(0.5)
    # time_pos_start = time.time()
    # rmi_send(sock, '{"Command": "FRC_ReadCartesianPosition"}\r\n')
    # # rmi_send(sock, '{"Command": "FRC_ReadJointAngles"}\r\n')
    # rmi_read(sock)
    # print(">>POS: ", time.time() - time_pos_start)

    # time.sleep(0.5)
    # time_reg_start = time.time()
    # rmi_send(sock, '{"Command": "FRC_ReadPositionRegister", "RegisterNumber": 1}\r\n')
    # rmi_read(sock)
    # print(">>REG: ", time.time() - time_reg_start)

    # time.sleep(0.5)

    close_connection(sock)

# ===== TEST MULTITHREADING =======================================================================

def test_multithreading_interface_sender(sock, stop_event, sequence_queue, sequence_lock, sequence):
    """Thread sending messages."""
    for _ in range(20):
        jump_distance = 5.0
        r = random.randint(1, 3)
        sign = random.randint(0, 1)
        if not sign: sign = -1
        
        with sequence_lock:
            sequence_queue.append(sequence)
            print("[QUEUE]", len(sequence_queue), sequence_queue)

        if r == 1:
            sequence = move_robot_cartesian_representation_with_socket(sock, sequence, 
                        is_motion_relative=True, x=sign*jump_distance, accuracy='CNT', wait_for_response=False)
        elif r == 2:
            sequence = move_robot_cartesian_representation_with_socket(sock, sequence, 
                        is_motion_relative=True, y=sign*jump_distance, accuracy='CNT', wait_for_response=False)
        else:
            sequence = move_robot_cartesian_representation_with_socket(sock, sequence, 
                        is_motion_relative=True, z=sign*jump_distance, accuracy='CNT', wait_for_response=False)
        time.sleep(0.1)

    with sequence_lock:
            sequence_queue.append(sequence)
            print("[QUEUE]", len(sequence_queue), sequence_queue)
            
    sequence = move_robot_cartesian_representation_with_socket(sock, sequence, 
                        is_motion_relative=True, z=50.0, wait_for_response=False)
    time.sleep(3)
    stop_event.set() # flag informing that all commands have been sent

def test_multithreading_interface_receiver(sock, stop_event, sequence_queue, sequence_lock):
    """Thread receiving messages."""
    while not stop_event.is_set():
        data = sock.recv(1024)
        if not data:
            print("Connection closed by server")
            break
        message = json.loads(data)

        seq = message.get("SequenceID", "NOSEQ")
        with sequence_lock:
            if seq in sequence_queue:
                sequence_queue.remove(seq)

        message_decoded = json.dumps(message, indent=2)
        print("[RECEIVER]", message_decoded)

def test_multithreading_interface():
    sequence_queue = []
    sequence_lock = threading.Lock()
    stop_event = threading.Event() # flag stopping both threads

    if USE_FAKE_SOCKET:
        # use simulated socket - local debug mode
        sock = FakeSocket()
    else:
        sock = initialize_connection()
    sequence = 1 # ID of the motion command in RMI sequence

    # go to start position
    sequence = home_robot_with_socket(sock, sequence, 50)

    t_send = threading.Thread(target=test_multithreading_interface_sender, args=(sock, stop_event, sequence_queue, sequence_lock, sequence), daemon=True)
    t_recv = threading.Thread(target=test_multithreading_interface_receiver, args=(sock, stop_event, sequence_queue, sequence_lock), daemon=True)

    t_send.start()
    t_recv.start()

    t_send.join()
    t_recv.join()

    close_connection(sock)

# ===== MAIN =======================================================================

if __name__ == "__main__":
    # get_robot_position()
    move_robot_to_home_position()
    # test_robot_motion_interface()
    # test_multithreading_interface()