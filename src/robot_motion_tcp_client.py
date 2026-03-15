from settings import *
from robot_motion_interface import *
from tcp_client import *

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

def test_robot_motion_tcp_client():

    new_port = get_new_port_number()
    client = TcpClient(IP_ADDRESS, new_port)
    #client.registerCallback(lambda: print("New message!"))

    client.writeMessage('{"Command": "FRC_Initialize"}\r\n'.encode())
    msg = client.readMessage()
    print(msg)

    # if client.hasData():
    #     msg = client.readMessage()
    #     print(msg)

    client.cancel()
    client.join(timeout=5.0)


# ===== MAIN =======================================================================

if __name__ == "__main__":
    test_robot_motion_tcp_client()