from settings import *
from robot_motion_interface import *
from tcp_client import *

# ===== CONNECTION =======================================================================

def get_new_port_number() -> int:
    # get port to create connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((IP_ADDRESS, PORT_CONNECTION_PROCEDURE))
        rmi_send(sock, '{"Communication": "FRC_Connect"}\r\n')
        error_id, msg = rmi_read(sock)

        if error_id == 0:
            print("Connected")

        # read port num  
        port_num = msg["PortNumber"]
    return port_num

def send_message(client: TcpClient, message: str) -> None: 
    """Encode and send a message over an RMI socket."""
    client.writeMessage(message.encode())

def get_message(client: TcpClient): 
    """Receive and decode a JSON message from an RMI socket.
    Return: error_id nad message.
    """
    data = client.readMessage()

    messages = [] 
    for line in data.splitlines(): 
        if line.strip(): 
            message = json.loads(line)

            error_id = message["ErrorID"]
            decode_error_id(error_id)
            
            messages.append(message) 

    message_decoded = json.dumps(messages, indent=2)
    print(message_decoded)

    return error_id, message

# ===== MOVEMENT =======================================================================

# ===== TESTS =======================================================================

def test_robot_motion_tcp_client():

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
        error_id, msg = get_message(client)
        if error_id == 0:
            print("Initialized")
            time.sleep(0.1)
        else:
            time.sleep(2)

    # while client.hasData():
    #     time.sleep(0.1)
    #     msg = client.readMessage()
    #     print(msg)


    # cancel all commands
    send_message(client, '{"Command": "FRC_Abort"}\r\n')
    time.sleep(0.1)
    get_message(client)
    time.sleep(0.1)

    # close the connection on robot side
    send_message(client, '{"Communication": "FRC_Disconnect"}\r\n')
    time.sleep(0.1)
    get_message(client)
    time.sleep(0.1)

    client.cancel()
    client.join(timeout=5.0)


# ===== MAIN =======================================================================

if __name__ == "__main__":
    test_robot_motion_tcp_client()