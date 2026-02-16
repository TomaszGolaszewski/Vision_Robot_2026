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
    message = json.loads(data)
    print(message)
    message_decoded = json.dumps(message, indent=2)
    # print (rcv)

    return message

def move_robot_joint_relative(sock: socket.socket, j1: float = 0.0, j2: float = 0.0, j3: float = 0.0, 
                        j4: float = 0.0, j5: float = 0.0, j6: float = 0.0, speed: int = 50):

    motion_dict = copy.deepcopy(frc_joint_motion_dict)

    # Adjust position
    motion_dict["JointAngle"]["J1"] = j1
    motion_dict["JointAngle"]["J2"] = j2
    motion_dict["JointAngle"]["J3"] = j3
    motion_dict["JointAngle"]["J4"] = j4
    motion_dict["JointAngle"]["J5"] = j5
    motion_dict["JointAngle"]["J6"] = j6
    motion_dict["SequenceID"] = 1
    motion_dict["Speed"] = speed

    motion_json = json.dumps(motion_dict, indent=2)
    motion_json = motion_json + "\r\n"

    rmi_send(sock, motion_json.encode())
    rmi_read(sock)

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

        rmi_send(s2, '{"Command": "FRC_Initialize"}\r\n')
        rmi_read(s2)

        time.sleep(10)
        move_robot_joint_relative(s2, j1 = 10.0)
        time.sleep(10)
        move_robot_joint_relative(s2, j3 = 10.0)
        time.sleep(10)
        move_robot_joint_relative(s2, j1 = -10.0)
        time.sleep(10)
        move_robot_joint_relative(s2, j3 = -10.0)
        time.sleep(10)

        rmi_send(s2, '{"Command": "FRC_Abort"}\r\n')
        rmi_read(s2)
        time.sleep(3)
        rmi_send(s2, '{"Communication": "FRC_Disconnect"}\r\n')
        rmi_read(s2)

if __name__ == "__main__":
    test_robot_motion_interface()