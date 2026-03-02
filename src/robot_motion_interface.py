import socket
import time
import json
import copy

# Global variables
IP_ADDRESS = '127.0.0.1'
PORT_CONNECTION_PROCEDURE = 16001

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
    sock.send(message.encode())

def rmi_read(sock: socket.socket) -> dict: 
    """Receive and decode a JSON message from an RMI socket.
    Return: error_id nad message.
    """
    data = sock.recv(1024)
    # print(data)
    message = json.loads(data)
    # print(message)
    message_decoded = json.dumps(message, indent=2)
    print(message_decoded)

    error_id = message["ErrorID"]
    if error_id == 7126:
        print("ERROR: 7126 - :)")
    elif error_id == 2556936:
        print("ERROR: 2556936 - TP enabled!")
    elif error_id == 2556937:
        print("ERROR: 2556937 - some errors on TP???")
    elif error_id == 2556943:
        print("ERROR: 2556943 - Last connection was not aborted!")
    elif error_id == 2556956:
        print("ERROR: 2556956 - motion aborted???")
    elif error_id == 2556957:
        print("ERROR: 2556957 - Invalid SequenceID or RMI_MOVE program is open!")

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
    time.sleep(1)

    # initialize connection
    error_id = 1
    while error_id:
        rmi_send(s2, '{"Command": "FRC_Initialize"}\r\n')
        error_id, msg = rmi_read(s2)
        if error_id == 0:
            print("Initialized")
            time.sleep(1)
        else:
            time.sleep(2)

    return s2

def close_connection(sock: socket.socket):

    # cancel all commands
    time.sleep(1)
    rmi_send(sock, '{"Command": "FRC_Abort"}\r\n')
    rmi_read(sock)

    # close the connection on robot side
    time.sleep(1)
    rmi_send(sock, '{"Communication": "FRC_Disconnect"}\r\n')
    rmi_read(sock)

    # close the connection on our side
    time.sleep(1)
    sock.close()

# ===== MOVEMENT =======================================================================

def move_robot_joint_representation(sock: socket.socket, sequence: int, is_motion_relative: bool = False, 
                        j1: float = 0.0, j2: float = 0.0, j3: float = 0.0, 
                        j4: float = 0.0, j5: float = 0.0, j6: float = 0.0, 
                        speed: int = 100, accuracy: str = 'FINE') -> int:

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
    rmi_read(sock)

    return sequence + 1

def move_robot_cartesian_representation(sock: socket.socket, sequence: int, is_motion_relative: bool = False, 
                        x: float = 0.0, y: float = 0.0, z: float = 0.0, 
                        w: float = 0.0, p: float = 0.0, r: float = 0.0, 
                        speed: int = 100, accuracy: str = 'FINE') -> int:

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
    rmi_read(sock)

    return sequence + 1

# ===== TESTS =======================================================================

def test_robot_motion_interface():

    sock = initialize_connection()

     # go to start position
    sequence = 1 # ID of the motion command in RMI sequence
    rmi_send(sock, '{"Command" : "FRC_SetOverRide", "Value" : 10 } \r\n')
    rmi_read(sock)
    sequence = move_robot_joint_representation(sock, sequence, 
                                        j1=-40.0, j2=5.0, j3=-30.0, j4=-90.0, j5=-80.0, j6=100.0)
    time.sleep(1)
    rmi_send(sock, '{"Command" : "FRC_SetOverRide", "Value" : 50 } \r\n')
    rmi_read(sock)

    for _ in range(2):
        sequence = move_robot_cartesian_representation(sock, sequence, is_motion_relative=True, x=200.0, accuracy='CNT')
        sequence = move_robot_cartesian_representation(sock, sequence, is_motion_relative=True, y=200.0, accuracy='CNT')
        sequence = move_robot_cartesian_representation(sock, sequence, is_motion_relative=True, x=-200.0, accuracy='CNT')
        sequence = move_robot_cartesian_representation(sock, sequence, is_motion_relative=True, y=-200.0, accuracy='CNT')

    close_connection(sock)


def test_robot_motion_interface_old():
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

if __name__ == "__main__":
    test_robot_motion_interface()