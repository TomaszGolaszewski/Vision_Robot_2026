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
        "UFrameNumber": 1,
        "Front": 1, 
        "Up": 1,
        "Left": 0, 
        "Flip": 1,
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


def rmi_send(sock: socket.socket, message: str) -> None: 
    """Encode and send a message over an RMI socket."""
    sock.send(message.encode())

def rmi_read(sock: socket.socket) -> dict: 
    """Receive and decode a JSON message from an RMI socket."""
    data = sock.recv(1024)
    # print(data)
    message = json.loads(data)
    # print(message)
    message_decoded = json.dumps(message, indent=2)
    print(message_decoded)

    return message

def move_robot_joint_representation(sock: socket.socket, sequence: int, is_motion_relative: bool = False, 
                        j1: float = 0.0, j2: float = 0.0, j3: float = 0.0, 
                        j4: float = 0.0, j5: float = 0.0, j6: float = 0.0, 
                        speed: int = 100) -> int:

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

    motion_json = json.dumps(motion_dict, indent=2)
    motion_json = motion_json + "\r\n"

    rmi_send(sock, motion_json)
    rmi_read(sock)

    return sequence + 1

def move_robot_cartesian_representation(sock: socket.socket, sequence: int, is_motion_relative: bool = False, 
                        x: float = 0.0, y: float = 0.0, z: float = 0.0, 
                        w: float = 0.0, p: float = 0.0, r: float = 0.0, 
                        speed: int = 100) -> int:

    motion_dict = copy.deepcopy(FRC_CARTESIAN_REPRESENTATION_TEMPLATE_DICT)

    motion_dict["Instruction"] = "FRC_JointRelative" if is_motion_relative else "FRC_JointMotion"
    motion_dict["SequenceID"] = sequence
    motion_dict["Position"]["X"] = x
    motion_dict["Position"]["Y"] = y
    motion_dict["Position"]["Z"] = z
    motion_dict["Position"]["W"] = w
    motion_dict["Position"]["P"] = p
    motion_dict["Position"]["R"] = r
    motion_dict["Speed"] = speed

    motion_json = json.dumps(motion_dict, indent=2)
    motion_json = motion_json + "\r\n"

    rmi_send(sock, motion_json)
    rmi_read(sock)

    return sequence + 1

# ===== TESTS =================================================

def test_robot_motion_interface():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.connect((IP_ADDRESS, PORT_CONNECTION_PROCEDURE))
        rmi_send(s1, '{"Communication": "FRC_Connect"}\r\n')
        msg = rmi_read(s1)
        
        error_id = msg["ErrorID"]
        if error_id == 0:
            print("Connected")

        # read port num  
        port_num = msg["PortNumber"]

    time.sleep(3)

    # set new connection with new port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
        s2.connect((IP_ADDRESS, port_num))

        rmi_send(s2, '{"Command" : "FRC_ReadError" } \r\n')
        msg = rmi_read(s2)
        time.sleep(5)
        rmi_send(s2, '{"Command" : "FRC_GetStatus"} \r\n')
        msg = rmi_read(s2)
        time.sleep(5)
        
        error_id = 1
        while error_id:
            rmi_send(s2, '{"Command": "FRC_Initialize"}\r\n')
            msg = rmi_read(s2)
            error_id = msg["ErrorID"]
            if error_id == 0:
                print("Initialized")
            elif error_id == 7126:
                print("ERROR: 7126 - :)")
            elif error_id == 2556936:
                print("ERROR: 2556936 - TP enabled")
            elif error_id == 2556943:
                print("ERROR: 2556943 - Last connection was not aborted")
            elif error_id == 2556957:
                print("ERROR: 2556957 - Invalid SequenceID")
            time.sleep(5)

        time.sleep(10)
        sequence = 1 # ID of the motion command in RMI sequence
        sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j1=10.0)
        time.sleep(3)
        sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j3=10.0)
        time.sleep(3)
        sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j1=-10.0)
        time.sleep(3)
        sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j3=-10.0)
        time.sleep(3)

        rmi_send(s2, '{"Command" : "FRC_SetOverRide", "Value" : 100 } \r\n')
        msg = rmi_read(s2)
        
        for _ in range(2):
            sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j1=20.0)
            sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j3=-20.0)
            sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j1=-20.0)
            sequence = move_robot_joint_representation(s2, sequence, is_motion_relative=True, j3=20.0)

        # time.sleep(10)
        # sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative = True, x = 100) 
        # time.sleep(3)
        # sequence = move_robot_cartesian_representation(s2, sequence, is_motion_relative = True, x = -100) 
        # time.sleep(10)

        rmi_send(s2, '{"Command": "FRC_Abort"}\r\n')
        rmi_read(s2)
        time.sleep(3)
        rmi_send(s2, '{"Communication": "FRC_Disconnect"}\r\n')
        rmi_read(s2)

if __name__ == "__main__":
    test_robot_motion_interface()