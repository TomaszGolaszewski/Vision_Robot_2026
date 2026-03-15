"""
Thread-safe TCP client with queued messaging and optional receive callback.
"""

import socket
import struct
import threading
import queue
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Wire format: each message is prefixed with a 4-byte big-endian unsigned int
# indicating the payload length. This allows reliable framing over a stream socket.
_HEADER_FORMAT = ">I"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)

_RECV_QUEUE_MAXSIZE = 64
_SEND_QUEUE_MAXSIZE = 64
_QUEUE_TIMEOUT_S = 0.1


class TcpClient:
    """Bidirectional TCP client with non-blocking, thread-safe message queues.

    Internally maintains two daemon threads—one for reading from the socket,
    one for writing—so that callers are never blocked by network I/O.  All
    public methods are safe to call from any thread simultaneously.

    Wire protocol
    -------------
    Every message is framed as::

        [4-byte big-endian length][<length> bytes of payload]

    Both sides of the connection must speak the same protocol.

    Parameters
    ----------
    host:
        Hostname or IP address of the remote endpoint.
    port:
        TCP port number of the remote endpoint.
    recv_queue_maxsize:
        Upper bound on queued inbound messages.  When the queue is full the
        reader thread drops the oldest message and logs a warning.
    """

    def __init__(
        self,
        host: str,
        port: int,
        recv_queue_maxsize: int = _RECV_QUEUE_MAXSIZE,
    ) -> None:
        self._host = host
        self._port = port

        self._sock: Optional[socket.socket] = None
        self._stop_event = threading.Event()

        self._recv_queue: queue.Queue = queue.Queue(maxsize=recv_queue_maxsize)
        self._send_queue: queue.Queue = queue.Queue(maxsize=_SEND_QUEUE_MAXSIZE)

        self._on_data_received: Optional[Callable[[], None]] = None
        self._callback_lock = threading.Lock()

        self._reader_thread = threading.Thread(
            target=self._reader_loop, name="TcpClient-reader", daemon=True
        )
        self._writer_thread = threading.Thread(
            target=self._writer_loop, name="TcpClient-writer", daemon=True
        )

        self._connect()

        self._reader_thread.start()
        self._writer_thread.start()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Signal both internal threads to stop and release the socket.

        Safe to call multiple times.  Returns immediately; use :meth:`join`
        to wait for the threads to finish.
        """
        self._stop_event.set()
        self._close_socket()

    def join(self, timeout: Optional[float] = None) -> None:
        """Block until both internal threads have terminated.

        Parameters
        ----------
        timeout:
            Maximum seconds to wait per thread.  ``None`` waits indefinitely.
        """
        self._reader_thread.join(timeout=timeout)
        self._writer_thread.join(timeout=timeout)

    def writeMessage(self, payload: bytes) -> None:
        """Enqueue *payload* for asynchronous delivery over the socket.

        Returns as soon as the message is placed in the outbound queue;
        actual transmission happens on the writer thread.

        Parameters
        ----------
        payload:
            Raw bytes to send.

        Raises
        ------
        RuntimeError
            If the client has been cancelled.
        queue.Full
            If the outbound queue is at capacity.
        """
        if self._stop_event.is_set():
            raise RuntimeError("TcpClient has been cancelled")
        self._send_queue.put_nowait(payload)

    def readMessage(self, block: bool = True, timeout: Optional[float] = None) -> bytes:
        """Return the next received message from the inbound queue.

        Parameters
        ----------
        block:
            If ``True`` (default), wait until a message is available.
        timeout:
            When *block* is ``True``, maximum seconds to wait.

        Returns
        -------
        bytes
            The raw payload of the next available message.

        Raises
        ------
        queue.Empty
            If no message is available within the given timeout.
        """
        return self._recv_queue.get(block=block, timeout=timeout)

    def hasData(self) -> bool:
        """Return ``True`` if at least one message is waiting in the inbound queue."""
        return not self._recv_queue.empty()

    def registerCallback(self, callback: Optional[Callable[[], None]]) -> None:
        """Register (or clear) a callable invoked whenever a message arrives.

        The callback is executed on the reader thread immediately after the
        message is placed in the inbound queue.  It must be lightweight and
        must not call :meth:`readMessage` in a blocking fashion from within
        itself to avoid deadlocks.

        Parameters
        ----------
        callback:
            A zero-argument callable, or ``None`` to remove a previously
            registered callback.
        """
        with self._callback_lock:
            self._on_data_received = callback

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.connect((self._host, self._port))
        self._sock = sock
        logger.info("Connected to %s:%d", self._host, self._port)

    def _close_socket(self) -> None:
        sock = self._sock
        if sock is None:
            return
        self._sock = None
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        finally:
            sock.close()

    # ------------------------------------------------------------------
    # Thread loops
    # ------------------------------------------------------------------

    def _reader_loop(self) -> None:
        """Continuously read framed messages from the socket."""
        try:
            while not self._stop_event.is_set():
                header = self._recv_exactly(_HEADER_SIZE)
                if header is None:
                    break

                (length,) = struct.unpack(_HEADER_FORMAT, header)
                payload = self._recv_exactly(length)
                if payload is None:
                    break

                self._enqueue_received(payload)
        except Exception as exc:
            if not self._stop_event.is_set():
                logger.error("Reader thread error: %s", exc)
        finally:
            self._stop_event.set()
            logger.debug("Reader thread exiting")

    def _writer_loop(self) -> None:
        """Drain the outbound queue and write framed messages to the socket."""
        try:
            # while not self._stop_event.is_set() or not self._send_queue.empty():
            while not self._stop_event.is_set():
                try:
                    payload = self._send_queue.get(timeout=_QUEUE_TIMEOUT_S)
                except queue.Empty:
                    continue

                frame = struct.pack(_HEADER_FORMAT, len(payload)) + payload
                self._send_all(frame)
        except Exception as exc:
            if not self._stop_event.is_set():
                logger.error("Writer thread error: %s", exc)
        finally:
            self._stop_event.set()
            logger.debug("Writer thread exiting")

    # ------------------------------------------------------------------
    # Low-level I/O
    # ------------------------------------------------------------------

    def _recv_exactly(self, n: int) -> Optional[bytes]:
        """Read exactly *n* bytes from the socket; return ``None`` on EOF or error."""
        buf = bytearray()
        while len(buf) < n:
            if self._stop_event.is_set():
                return None
            sock = self._sock
            if sock is None:
                return None
            try:
                chunk = sock.recv(n - len(buf))
            except OSError:
                return None
            if not chunk:
                return None
            buf.extend(chunk)
        return bytes(buf)

    def _send_all(self, data: bytes) -> None:
        """Write *data* to the socket in full, retrying on partial writes."""
        total = 0
        while total < len(data):
            sock = self._sock
            if sock is None or self._stop_event.is_set():
                raise OSError("Socket closed during send")
            sent = sock.send(data[total:])
            if sent == 0:
                raise OSError("Connection lost during send")
            total += sent

    def _enqueue_received(self, payload: bytes) -> None:
        """Place *payload* in the inbound queue, evicting the oldest entry if full."""
        try:
            self._recv_queue.put_nowait(payload)
        except queue.Full:
            try:
                dropped = self._recv_queue.get_nowait()
                logger.warning(
                    "Inbound queue full; dropped oldest message (%d bytes)", len(dropped)
                )
            except queue.Empty:
                pass
            self._recv_queue.put_nowait(payload)

        with self._callback_lock:
            cb = self._on_data_received
        if cb is not None:
            try:
                cb()
            except Exception as exc:
                logger.error("Exception in data-received callback: %s", exc)
