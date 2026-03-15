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

# ===== CONNECTION =======================================================================

def rmi_send(sock: socket.socket, message: str) -> None: 
    """Encode and send a message over an RMI socket."""
    print("[SENDER]", message)
    sock.send(message.encode())

def rmi_read(sock: socket.socket) -> dict: 
    """Receive and decode a JSON message from an RMI socket.
    Return: error_id nad message.
    """
    data = sock.recv(1024)

    messages = [] 
    for line in data.splitlines(): 
        if line.strip(): 
            message = json.loads(line)

            error_id = message["ErrorID"]
            if error_id == 7126:
                print("ERROR: 7126 - robot is not mastered or its program buffer is full ???")
            elif error_id == 7015:
                print("ERROR: 7015 - robot cannot move safely, you must select the program and move it manually to the home position ???")
            elif error_id == 2556936:
                print("ERROR: 2556936 - TP enabled!")
            elif error_id == 2556937:
                print("ERROR: 2556937 - some errors on TP???")
            elif error_id == 2556942:
                print("ERROR: 2556942 - robot cannot move safely, you must select the program and move it manually to the home position ???")
            elif error_id == 2556943:
                print("ERROR: 2556943 - Last connection was not aborted!")
            elif error_id == 2556956:
                print("ERROR: 2556956 - motion aborted???")
            elif error_id == 2556957:
                print("ERROR: 2556957 - Invalid SequenceID, length of path equals zero or RMI_MOVE program is open!")

            messages.append(message) 

    message_decoded = json.dumps(messages, indent=2)
    print(message_decoded)

    return error_id, message


def initialize_connection() -> socket.socket:

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

def move_robot_joint_representation(sock: socket.socket, sequence: int, is_motion_relative: bool = False, 
                        j1: float = 0.0, j2: float = 0.0, j3: float = 0.0, 
                        j4: float = 0.0, j5: float = 0.0, j6: float = 0.0, 
                        speed: int = 100, accuracy: str = 'FINE', wait_for_response: bool = True) -> int:

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

    motion_json = json.dumps(motion_dict, indent=2)
    motion_json = motion_json + "\r\n"

    rmi_send(sock, motion_json)
    if wait_for_response:
        rmi_read(sock)

    return sequence + 1

def move_robot_cartesian_representation(sock: socket.socket, sequence: int, is_motion_relative: bool = False, 
                        x: float = 0.0, y: float = 0.0, z: float = 0.0, 
                        w: float = 0.0, p: float = 0.0, r: float = 0.0, 
                        speed: int = 100, accuracy: str = 'FINE', wait_for_response: bool = True) -> int:

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

    motion_json = json.dumps(motion_dict, indent=2)
    motion_json = motion_json + "\r\n"

    rmi_send(sock, motion_json)
    if wait_for_response:
        rmi_read(sock)

    return sequence + 1

def home_robot(sock: socket.socket, sequence: int, speed: int = 100) -> int:
    """Move the robot to its HOME position."""
    rmi_send(sock, '{"Command" : "FRC_SetOverRide", "Value" : 10 } \r\n')
    rmi_read(sock)
    sequence = move_robot_joint_representation(sock, sequence, 
                                        j1=-50, j2=25.0, j3=-40.0, j4=-118.0, j5=-61.0, j6=-11)
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
    home_robot(sock, 1)
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
    sequence = home_robot(sock, sequence)

    for _ in range(20):
        r = random.randint(1, 3)
        sign = random.randint(0, 1)
        if not sign: sign = -1
        
        if r == 1:
            sequence = move_robot_cartesian_representation(sock, sequence, is_motion_relative=True, x=sign*5.0) #, accuracy='CNT')
        elif r == 2:
            sequence = move_robot_cartesian_representation(sock, sequence, is_motion_relative=True, y=sign*5.0) #, accuracy='CNT')
        else:
            sequence = move_robot_cartesian_representation(sock, sequence, is_motion_relative=True, z=sign*5.0) #, accuracy='CNT')

    close_connection(sock)


def test_robot_motion_interface_old():
    """Test connection with the robot and its functions."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.connect((IP_ADDRESS, PORT_CONNECTION_PROCEDURE))
        rmi_send(s1, '{"Communication": "FRC_Connect"}\r\n')
        error_id, msg = rmi_read(s1)

        if error_id == 0:
            print("Connected")

        # read port num  
        port_num = msg["PortNumber"]

    time.sleep(3)

    # set new connection with new port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
        s2.connect((IP_ADDRESS, port_num))

        time.sleep(1)
        rmi_send(s2, '{"Command": "FRC_Abort"}\r\n')
        rmi_read(s2)
        time.sleep(1)

        # rmi_send(s2, '{"Command" : "FRC_ReadError" } \r\n')
        # msg = rmi_read(s2)
        # time.sleep(1)

        # rmi_send(s2, '{"Command" : "FRC_GetStatus"} \r\n')
        # msg = rmi_read(s2)
        # time.sleep(1)
        # "TPMode": 0, - ok, "TPMode": 1, enabled

        # rmi_send(s2, '{"Command": "FRC_ReadCartesianPosition"}\r\n')
        # rmi_read(s2)
        # time.sleep(1)

        # rmi_send(s2, '{"Command": "FRC_ReadJointAngles"}\r\n')
        # rmi_read(s2)
        # time.sleep(1)
        
        error_id = 1
        while error_id:
            rmi_send(s2, '{"Command": "FRC_Initialize"}\r\n')
            error_id, msg = rmi_read(s2)
            if error_id == 0:
                print("Initialized")
                time.sleep(1)
            else:
                time.sleep(5)

        # go to start position
        sequence = 1 # ID of the motion command in RMI sequence
        rmi_send(s2, '{"Command" : "FRC_SetOverRide", "Value" : 10 } \r\n')
        rmi_read(s2)
        sequence = move_robot_joint_representation(s2, sequence, 
                                            j1=-40.0, j2=5.0, j3=-30.0, j4=-90.0, j5=-80.0, j6=100.0)
        time.sleep(1)
        rmi_send(s2, '{"Command" : "FRC_SetOverRide", "Value" : 50 } \r\n')
        rmi_read(s2)

        # sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j1=10.0)
        # time.sleep(3)
        # sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j3=10.0)
        # time.sleep(3)
        # sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j1=-10.0)
        # time.sleep(3)
        # sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j3=-10.0)
        # time.sleep(3)
        
        for _ in range(5):
            # sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j1=20.0, accuracy='CNT')
            # sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j3=-20.0, accuracy='CNT')
            # sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j1=-20.0, accuracy='CNT')
            # sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j3=20.0, accuracy='CNT')

            sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative=True, x=200.0, accuracy='CNT')
            sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative=True, y=200.0, accuracy='CNT')
            sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative=True, x=-200.0, accuracy='CNT')
            sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative=True, y=-200.0, accuracy='CNT')

            # sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative=True, w=10.0)
            # sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative=True, w=-10.0)
            # sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative=True, p=10.0)
            # sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative=True, p=-10.0)
            # sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative=True, r=10.0)
            # sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative=True, r=-10.0)

            # sequence = move_robot_cartesian_representation(s2, sequence, 
            #                           x=640.0, y=-50.0, z=300.0, w=-100.0, p=-70.0, r=-35.0, accuracy='CNT')
            # sequence = move_robot_cartesian_representation(s2, sequence, 
            #                           x=640.0, y=-50.0, z=400.0, w=-100.0, p=-70.0, r=-35.0, accuracy='CNT')
            # sequence = move_robot_cartesian_representation(s2, sequence, 
            #                           x=640.0, y=-150.0, z=400.0, w=-100.0, p=-70.0, r=-35.0, accuracy='CNT')
            # sequence = move_robot_cartesian_representation(s2, sequence, 
            #                           x=640.0, y=-150.0, z=300.0, w=-100.0, p=-70.0, r=-35.0, accuracy='CNT')

        time.sleep(3)
        rmi_send(s2, '{"Command": "FRC_Abort"}\r\n')
        rmi_read(s2)
        time.sleep(1)
        rmi_send(s2, '{"Communication": "FRC_Disconnect"}\r\n')
        rmi_read(s2)

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
            sequence = move_robot_cartesian_representation(sock, sequence, 
                        is_motion_relative=True, x=sign*jump_distance, accuracy='CNT', wait_for_response=False)
        elif r == 2:
            sequence = move_robot_cartesian_representation(sock, sequence, 
                        is_motion_relative=True, y=sign*jump_distance, accuracy='CNT', wait_for_response=False)
        else:
            sequence = move_robot_cartesian_representation(sock, sequence, 
                        is_motion_relative=True, z=sign*jump_distance, accuracy='CNT', wait_for_response=False)
        time.sleep(0.1)

    with sequence_lock:
            sequence_queue.append(sequence)
            print("[QUEUE]", len(sequence_queue), sequence_queue)
            
    sequence = move_robot_cartesian_representation(sock, sequence, 
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
    sequence = home_robot(sock, sequence, 50)

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
    # move_robot_to_home_position()
    # test_robot_motion_interface()
    test_multithreading_interface()