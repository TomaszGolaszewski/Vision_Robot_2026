from settings import *
from robot_motion_interface import *
from tcp_client import *


# ===== PARAMETRES =======================================================================

def request_status(client: TcpClient) -> None: 
    """Reqests robot's current position and data from the robot's position register."""

    send_message(client, '{"Command": "FRC_ReadCartesianPosition"}\r\n')
    send_message(client, '{"Command": "FRC_ReadPositionRegister", "RegisterNumber":%s}\r\n' % REGISTER_NUMBER)

def parse_coordinates(position_to_parse: json, coordinates: list) -> None: 
    """Extracts coordinate values from a JSON-like object and writes them into a list."""
    coordinates[0] = position_to_parse.get("X", 0)
    coordinates[1] = position_to_parse.get("Y", 0)
    coordinates[2] = position_to_parse.get("Z", 0)
    coordinates[3] = position_to_parse.get("W", 0)
    coordinates[4] = position_to_parse.get("P", 0)
    coordinates[5] = position_to_parse.get("R", 0)

# ===== CONNECTION =======================================================================

def get_new_port_number() -> int:
    """Connect to the robot to get the new port number."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((IP_ADDRESS, PORT_CONNECTION_PROCEDURE))
        rmi_send(sock, '{"Communication": "FRC_Connect"}\r\n')
        error_id, msg = rmi_read(sock)

        if error_id == 0:
            print("[STATUS] Connected")

        # read port num  
        port_num = msg["PortNumber"]
    return port_num

def send_message(client: TcpClient, message: str) -> None: 
    """Encode and send a message over an RMI socket."""
    client.writeMessage(message.encode())

def get_message(client: TcpClient, print_message: bool = False) -> list: 
    """Receive and decode a JSON message from an RMI TCP client.
    Return: list of error_ids.
    """
    data = client.readMessage()

    messages = [] 
    error_list = []
    for line in data.splitlines(): 
        if line.strip(): 
            message = json.loads(line)
            messages.append(message) 

            if message.get("ErrorID", None) is not None:
                error_id = message["ErrorID"]
                error_list.append(error_id)
                decode_error_id(error_id)
            else:
                print(json.dumps(message, indent=2))
    
    if print_message:
        message_decoded = json.dumps(messages, indent=2)
        print(message_decoded)

    return error_list

def get_and_handle_message_for_robot_motion(client: TcpClient, 
                    robot_position: list, robot_forces: list, sequence_queue: list,
                    print_message: bool = False) -> list:
    """Receive and decode a JSON message from an RMI TCP client.
    Return: list of sequence ids waiting in the queue.
    """
    sequence_list = []
    while client.hasData():
        data = client.readMessage()
        messages = [] 
        error_list = []

        for line in data.splitlines(): 
            if line.strip(): 
                message = json.loads(line)
                messages.append(message) 

                if message.get("ErrorID", None) is not None:
                    error_id = message["ErrorID"]
                    error_list.append(error_id)
                    decode_error_id(error_id)
                else:
                    print(json.dumps(message, indent=2))

                sequence_id = message.get("SequenceID", None)
                if sequence_id:
                    sequence_list.append(sequence_id)

                command = message.get("Command", None)
                position = message.get("Position", None)
                if command == "FRC_ReadCartesianPosition" and position:
                    parse_coordinates(position, robot_position)
                if command == "FRC_ReadPositionRegister" and position:
                    parse_coordinates(position, robot_forces)
    
        if print_message:
            message_decoded = json.dumps(messages, indent=2)
            print(message_decoded)
    
    return [s for s in sequence_queue if s not in sequence_list]

def initialize_connection_with_tcp_client() -> TcpClient:
    """Create TCP client object, wait until all errors on robot are resolved and initialize the connection.
    Return connected TCP client object."""

    new_port = get_new_port_number()
    time.sleep(0.1)
    client = TcpClient(IP_ADDRESS, new_port)
    #client.registerCallback(lambda: print("New message!"))
    time.sleep(0.1)

    # cancel all old commands
    send_message(client, '{"Command": "FRC_Abort"}\r\n')
    time.sleep(0.1)
    get_message(client)
    time.sleep(0.1)

    # initialize connection
    error_id = 1
    while error_id:
        send_message(client, '{"Command": "FRC_Initialize"}\r\n')
        time.sleep(0.1)
        error_list = get_message(client)
        error_id = error_list[0]
        if error_id == 0:
            print("[STATUS] Initialized")
            time.sleep(0.1)
        else:
            time.sleep(2)

    return client

def close_connection_with_tcp_client(client: TcpClient) -> None:
    """Cancel all commands, close the connection to the robot and close the TCP client."""

    time.sleep(0.1)

    # cancel all commands
    send_message(client, '{"Command": "FRC_Abort"}\r\n')
    time.sleep(0.1)
    get_message(client)
    time.sleep(0.1)

    # close the connection on robot side
    send_message(client, '{"Communication": "FRC_Disconnect"}\r\n')
    time.sleep(0.1)
    error_list = get_message(client)
    if error_list[0] == 0:
        print("[STATUS] Disconnected")
    time.sleep(0.1)

    client.cancel()
    client.join(timeout=5.0)

# ===== MOVEMENT =======================================================================

def move_robot_joint_representation_with_tcp_client(client: TcpClient, sequence: int, is_motion_relative: bool = False, 
                        j1: float = 0.0, j2: float = 0.0, j3: float = 0.0, 
                        j4: float = 0.0, j5: float = 0.0, j6: float = 0.0, 
                        speed: int = 100, accuracy: str = 'FINE', wait_for_response: bool = False) -> int:

    motion_json = prepare_command_move_robot_joint_representation(
                        sequence=sequence, is_motion_relative=is_motion_relative,
                        j1=j1, j2=j2, j3=j3, j4=j4, j5=j5, j6=j6, speed=speed, accuracy=accuracy)

    send_message(client, motion_json)
    if wait_for_response:
        time.sleep(1)
        get_message(client)

    return sequence + 1

def move_robot_cartesian_representation_with_tcp_client(client: TcpClient, sequence: int, is_motion_relative: bool = False, 
                        x: float = 0.0, y: float = 0.0, z: float = 0.0, 
                        w: float = 0.0, p: float = 0.0, r: float = 0.0, 
                        speed: int = 100, accuracy: str = 'FINE', wait_for_response: bool = False) -> int:

    motion_json = prepare_command_move_robot_cartesian_representation(
                        sequence=sequence, is_motion_relative=is_motion_relative,
                        x=x, y=y, z=z, w=w, p=p, r=r, speed=speed, accuracy=accuracy)

    send_message(client, motion_json)
    if wait_for_response:
        time.sleep(1)
        get_message(client)

    return sequence + 1

def home_robot_with_tcp_client(client: TcpClient, sequence: int, speed: int = 100) -> int:
    """Move the robot to its HOME position."""
    send_message(client, '{"Command" : "FRC_SetOverRide", "Value" : 10 } \r\n')
    time.sleep(0.1)
    get_message(client)
    time.sleep(0.1)

    sequence = move_robot_joint_representation_with_tcp_client(client, sequence,
                                        **HOME_POSITION, wait_for_response=True)
    time.sleep(1)

    send_message(client, '{"Command" : "FRC_SetOverRide", "Value" : ' + str(speed) + ' } \r\n')
    time.sleep(0.1)
    get_message(client)
    time.sleep(0.1)

    return sequence

# ===== TESTS =======================================================================

def test_robot_motion_tcp_client():
    """Test connection via TCP client with the robot and its functions."""

    robot_current_position = [0, 0, 0, 0, 0, 0]
    robot_current_forces = [0, 0, 0, 0, 0, 0]
    sequence_queue = []
    sequence = 1 # ID of the motion command in RMI sequence

    client = initialize_connection_with_tcp_client()

    # go to start position
    sequence = home_robot_with_tcp_client(client, sequence, 50)

    for _ in range(50):
        jump_distance = 5.0
        r = random.randint(1, 3)
        sign = random.randint(0, 1)
        if not sign: sign = -1
        
        request_status(client)
        time.sleep(0.02) # time needed to receive response
        sequence_queue = get_and_handle_message_for_robot_motion(client, 
                    robot_current_position, robot_current_forces, sequence_queue)
            
        sequence_queue.append(sequence)
        print("[QUEUE]", len(sequence_queue), sequence_queue)
        print("[POSITION]", robot_current_position)
        # print("[FORCES]", robot_current_forces)
        if r == 1:
            sequence = move_robot_cartesian_representation_with_tcp_client(client, sequence, 
                        is_motion_relative=True, x=sign*jump_distance, accuracy='CNT')
        elif r == 2:
            sequence = move_robot_cartesian_representation_with_tcp_client(client, sequence, 
                        is_motion_relative=True, y=sign*jump_distance, accuracy='CNT')
        else:
            sequence = move_robot_cartesian_representation_with_tcp_client(client, sequence, 
                        is_motion_relative=True, z=sign*jump_distance, accuracy='CNT')
        time.sleep(0.1)

    sequence_queue.append(sequence)
    print("[QUEUE]", len(sequence_queue), sequence_queue)
    sequence = move_robot_cartesian_representation_with_tcp_client(client, sequence,
                        is_motion_relative=True, z=50.0)
    time.sleep(2)

    sequence_queue = get_and_handle_message_for_robot_motion(client, 
                    robot_current_position, robot_current_forces, sequence_queue)
    print("[QUEUE]", len(sequence_queue), sequence_queue)

    close_connection_with_tcp_client(client)

# ===== MAIN =======================================================================

if __name__ == "__main__":
    test_robot_motion_tcp_client()