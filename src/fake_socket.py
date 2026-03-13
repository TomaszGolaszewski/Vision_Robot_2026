import json
from queue import Queue, Empty


class FakeSocket:
    """Local simulated TCP socket for debugging without a real server.

    This class simulates basic TCP socket behavior, allowing you to test
    communication logic without connecting to an actual server. Sent data
    is automatically transformed into a simple ACK-style response, and
    received data is retrieved from an internal queue.
    """

    def __init__(self):
        """Initializes the fake socket.

        Creates an internal queue for incoming data and marks the socket
        as open.
        """
        self.inbox = Queue()
        self.closed = False

    def send(self, data: bytes):
        """Simulates sending data.

        The method generates a response in the form ``b"ACK: " + data`` and
        places it into the internal receive queue.

        Args:
            data (bytes): The data to send.

        Returns:
            int: The number of bytes accepted for sending. Returns 0 if the
            socket is closed.
        """
        if self.closed:
            return 0
        
        # add ErrorID to return message
        decoded = data.decode().strip()
        cmd = json.loads(decoded)
        cmd["ErrorID"] = 0
        response = json.dumps(cmd)
        # response = b"ACK: " + data

        # insert new response into the internal receive queue
        self.inbox.put(response)
        return len(data)

    def recv(self, bufsize: int):
        """Simulates receiving data.

        Retrieves data from the internal queue. If no data arrives within
        the timeout period, an empty byte string is returned.

        Args:
            bufsize (int): Maximum number of bytes to receive. This parameter
                is ignored in this implementation and exists only for API
                compatibility.

        Returns:
            bytes: Received data, or an empty byte string if the socket is
            closed or no data is available.
        """
        if self.closed:
            return b""
        try:
            return self.inbox.get(timeout=1)
        except Empty:
            return b""

    def close(self):
        """Closes the socket.

        After closing, the socket no longer accepts or returns data.
        """
        self.closed = True
