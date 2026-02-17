import socket
import time
import json
import copy

IP_ADDRESS = '127.0.0.1'

# Movement instruction
frc_joint_motion_dict = {
    # "Instruction": "FRC_JointMotionJRep",
    "Instruction": "FRC_JointRelativeJRep",
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
    "TermType": "FINE",
    "TermValue": 0,
    "ACC": None,
    "OffsetPRNumber": None,
    "VisionPRNumber": None,
    "MROT": None,
    "LCBType": None,
    "LCBValue": None,
    "PortType": None,
    "portNumber": None,
    "portValue": None,
    "SequenceID": 0,
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

def move_robot_joint_relative(sock: socket.socket, sequence: int, j1: float = 0.0, j2: float = 0.0, j3: float = 0.0, 
                        j4: float = 0.0, j5: float = 0.0, j6: float = 0.0, speed: int = 50):

    motion_dict = copy.deepcopy(frc_joint_motion_dict)

    # Adjust position
    motion_dict["JointAngle"]["J1"] = j1
    motion_dict["JointAngle"]["J2"] = j2
    motion_dict["JointAngle"]["J3"] = j3
    motion_dict["JointAngle"]["J4"] = j4
    motion_dict["JointAngle"]["J5"] = j5
    motion_dict["JointAngle"]["J6"] = j6
    motion_dict["SequenceID"] = sequence
    motion_dict["Speed"] = speed

    motion_json = json.dumps(motion_dict, indent=2)
    motion_json = motion_json + "\r\n"

    rmi_send(sock, motion_json)
    rmi_read(sock)

    return sequence + 1

# ===== TESTS =================================================

def test_robot_motion_interface():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.connect((IP_ADDRESS, 16001))
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
        sequence = move_robot_joint_relative(s2, sequence, j1=10.0)
        time.sleep(3)
        sequence = move_robot_joint_relative(s2, sequence, j3=10.0)
        time.sleep(3)
        sequence = move_robot_joint_relative(s2, sequence, j1=-10.0)
        time.sleep(3)
        sequence = move_robot_joint_relative(s2, sequence, j3=-10.0)
        time.sleep(3)

        for i in range(3):
            sequence = move_robot_joint_relative(s2, sequence, j1=20.0, speed=100)
            sequence = move_robot_joint_relative(s2, sequence, j3=-20.0, speed=100)
            sequence = move_robot_joint_relative(s2, sequence, j1=-20.0, speed=100)
            sequence = move_robot_joint_relative(s2, sequence, j3=20.0, speed=100)

        rmi_send(s2, '{"Command": "FRC_Abort"}\r\n')
        rmi_read(s2)
        time.sleep(3)
        rmi_send(s2, '{"Communication": "FRC_Disconnect"}\r\n')
        rmi_read(s2)

if __name__ == "__main__":
    test_robot_motion_interface()