"""
FIX protocol client with session management.

Provides a base class for connecting to a FIX counterparty, managing
logon/logout handshakes, heartbeat monitoring, and sequence number
tracking.  Designed for subclassing — override the ``on_*`` hooks to
implement custom business logic.
"""

from __future__ import annotations

import logging
import socket
import threading
import time
from typing import Callable, Optional

from fix_protocol.fix_constants import MsgType, Tags
from fix_protocol.fix_message import FIXMessage
from fix_protocol.fix_translator import FIXTagTranslator

logger = logging.getLogger(__name__)


class FIXClient:
    """FIX 4.2 session client.

    Parameters
    ----------
    sender_comp_id : str
        The SenderCompID for outgoing messages.
    target_comp_id : str
        The TargetCompID for outgoing messages.
    host : str
        FIX counterparty hostname or IP.
    port : int
        FIX counterparty port.
    heartbeat_interval : int
        Heartbeat interval in seconds (default 30).
    translator : FIXTagTranslator, optional
        Tag translator instance; a default one is created if omitted.

    Example::

        client = FIXClient("MY_SENDER", "MY_TARGET", "fix.example.com", 9876)
        client.connect()
        client.logon()
        # ... send orders, etc. ...
        client.logout()
        client.disconnect()
    """

    # Buffer size for socket reads
    _RECV_BUFFER = 4096

    def __init__(
        self,
        sender_comp_id: str,
        target_comp_id: str,
        host: str,
        port: int,
        heartbeat_interval: int = 30,
        translator: Optional[FIXTagTranslator] = None,
    ) -> None:
        self.sender_comp_id = sender_comp_id
        self.target_comp_id = target_comp_id
        self.host = host
        self.port = port
        self.heartbeat_interval = heartbeat_interval
        self.translator = translator or FIXTagTranslator()

        # Session state
        self._send_seq_num = 1
        self._recv_seq_num = 1
        self._logged_in = False
        self._running = False

        # Networking
        self._socket: Optional[socket.socket] = None
        self._recv_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Timestamps for heartbeat monitoring
        self._last_send_time: float = 0.0
        self._last_recv_time: float = 0.0

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self, timeout: float = 10.0) -> None:
        """Open a TCP connection to the FIX counterparty.

        Raises :class:`ConnectionError` on failure.
        """
        logger.info("Connecting to %s:%d ...", self.host, self.port)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.host, self.port))
            self._socket = sock
            self._running = True

            # Start receiver thread
            self._recv_thread = threading.Thread(
                target=self._receive_loop, daemon=True, name="fix-recv"
            )
            self._recv_thread.start()

            logger.info("Connected to %s:%d", self.host, self.port)
        except OSError as exc:
            raise ConnectionError(
                f"Failed to connect to {self.host}:{self.port}: {exc}"
            ) from exc

    def disconnect(self) -> None:
        """Close the TCP connection and stop background threads."""
        self._running = False
        self._logged_in = False
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._socket.close()
            self._socket = None
        if self._recv_thread and self._recv_thread.is_alive():
            self._recv_thread.join(timeout=5)
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=5)
        logger.info("Disconnected")

    @property
    def is_connected(self) -> bool:
        """Return ``True`` if the TCP socket is open."""
        return self._socket is not None and self._running

    @property
    def is_logged_in(self) -> bool:
        """Return ``True`` if the FIX session is logged on."""
        return self._logged_in

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def logon(self, reset_seq: bool = False) -> None:
        """Send a Logon message to initiate the FIX session."""
        if reset_seq:
            self._send_seq_num = 1
        msg = FIXMessage.create_logon(
            self.sender_comp_id,
            self.target_comp_id,
            self._next_send_seq(),
            self.heartbeat_interval,
            reset_seq=reset_seq,
        )
        self._send_raw(msg)
        logger.info("Logon sent (seq=%d)", self._send_seq_num - 1)

    def logout(self, text: str = "") -> None:
        """Send a Logout message to terminate the FIX session."""
        msg = FIXMessage.create_logout(
            self.sender_comp_id,
            self.target_comp_id,
            self._next_send_seq(),
            text=text,
        )
        self._send_raw(msg)
        self._logged_in = False
        logger.info("Logout sent (seq=%d)", self._send_seq_num - 1)

    # ------------------------------------------------------------------
    # Sending messages
    # ------------------------------------------------------------------

    def send_message(self, msg: FIXMessage) -> None:
        """Send a pre-built :class:`FIXMessage`.

        Automatically fills in SenderCompID, TargetCompID, MsgSeqNum,
        and SendingTime if they are not already set.
        """
        if msg.get_field(Tags.SenderCompID) is None:
            msg.set_field(Tags.SenderCompID, self.sender_comp_id)
        if msg.get_field(Tags.TargetCompID) is None:
            msg.set_field(Tags.TargetCompID, self.target_comp_id)
        if msg.get_field(Tags.MsgSeqNum) is None:
            msg.set_field(Tags.MsgSeqNum, self._next_send_seq())
        if msg.get_field(Tags.SendingTime) is None:
            msg.set_field(Tags.SendingTime, FIXMessage._utc_timestamp())
        self._send_raw(msg)

    def send_new_order_single(
        self,
        cl_ord_id: str,
        symbol: str,
        side: str,
        order_qty: int,
        ord_type: str,
        price: Optional[float] = None,
        **kwargs,
    ) -> None:
        """Convenience: build and send a NewOrderSingle."""
        msg = FIXMessage.create_new_order_single(
            self.sender_comp_id,
            self.target_comp_id,
            self._next_send_seq(),
            cl_ord_id,
            symbol,
            side,
            order_qty,
            ord_type,
            price,
            **kwargs,
        )
        self._send_raw(msg)
        logger.info(
            "NewOrderSingle sent: %s %s %s qty=%d",
            cl_ord_id, symbol, side, order_qty,
        )

    def send_order_cancel(
        self,
        cl_ord_id: str,
        orig_cl_ord_id: str,
        symbol: str,
        side: str,
        order_qty: int,
    ) -> None:
        """Convenience: build and send an OrderCancelRequest."""
        msg = FIXMessage.create_order_cancel_request(
            self.sender_comp_id,
            self.target_comp_id,
            self._next_send_seq(),
            cl_ord_id,
            orig_cl_ord_id,
            symbol,
            side,
            order_qty,
        )
        self._send_raw(msg)
        logger.info("OrderCancelRequest sent: %s", cl_ord_id)

    # ------------------------------------------------------------------
    # Subclass hooks (override these for custom behaviour)
    # ------------------------------------------------------------------

    def on_logon(self, msg: FIXMessage) -> None:
        """Called when a Logon response is received.  Override in subclass."""
        logger.info("Logon acknowledged by counterparty")

    def on_logout(self, msg: FIXMessage) -> None:
        """Called when a Logout message is received.  Override in subclass."""
        logger.info("Logout received from counterparty")

    def on_execution_report(self, msg: FIXMessage) -> None:
        """Called when an ExecutionReport (MsgType=8) is received."""
        exec_type = msg.get_field(Tags.ExecType) or "?"
        order_id = msg.get_field(Tags.OrderID) or "?"
        logger.info("ExecutionReport: OrderID=%s ExecType=%s", order_id, exec_type)

    def on_order_cancel_reject(self, msg: FIXMessage) -> None:
        """Called when an OrderCancelReject (MsgType=9) is received."""
        cl_ord_id = msg.get_field(Tags.ClOrdID) or "?"
        logger.info("OrderCancelReject: ClOrdID=%s", cl_ord_id)

    def on_message(self, msg: FIXMessage) -> None:
        """Called for every inbound message *after* session-level handling.

        Override to implement custom message routing.
        """
        pass

    def on_error(self, error: Exception) -> None:
        """Called when an error occurs in the receive loop."""
        logger.error("FIX session error: %s", error)

    # ------------------------------------------------------------------
    # Translation helper
    # ------------------------------------------------------------------

    def translate_message(self, msg: FIXMessage) -> list[str]:
        """Translate a FIXMessage's fields to human-readable English strings.

        Uses the configured :class:`FIXTagTranslator`.
        """
        return self.translator.translate_message(msg.to_pairs())

    # ------------------------------------------------------------------
    # Internal — networking
    # ------------------------------------------------------------------

    def _send_raw(self, msg: FIXMessage) -> None:
        """Encode and send a message over the socket."""
        if self._socket is None:
            raise ConnectionError("Not connected")
        data = msg.encode()
        with self._lock:
            self._socket.sendall(data)
            self._last_send_time = time.monotonic()
        logger.debug("SENT: %s", data)

    def _receive_loop(self) -> None:
        """Background thread: read from socket and dispatch messages."""
        buf = b""
        while self._running and self._socket:
            try:
                self._socket.settimeout(1.0)
                chunk = self._socket.recv(self._RECV_BUFFER)
                if not chunk:
                    logger.warning("Connection closed by counterparty")
                    self._running = False
                    break
                buf += chunk
                self._last_recv_time = time.monotonic()

                # Extract complete messages (delimited by 10=xxx\x01)
                while True:
                    end = buf.find(b"\x0110=")
                    if end == -1:
                        break
                    # Find the SOH after the checksum value
                    cs_end = buf.find(b"\x01", end + 4)
                    if cs_end == -1:
                        break
                    raw_msg = buf[: cs_end + 1]
                    buf = buf[cs_end + 1:]
                    self._handle_raw_message(raw_msg)
            except socket.timeout:
                continue
            except OSError:
                if self._running:
                    logger.warning("Socket error in receive loop")
                break

    def _handle_raw_message(self, data: bytes) -> None:
        """Parse a raw message and route it to the appropriate handler."""
        try:
            msg = FIXMessage.decode(data)
        except Exception as exc:
            self.on_error(exc)
            return

        # Update expected receive sequence number
        seq = msg.get_field(Tags.MsgSeqNum)
        if seq is not None:
            self._recv_seq_num = int(seq) + 1

        msg_type = msg.get_field(Tags.MsgType)
        logger.debug("RECV MsgType=%s", msg_type)

        # Session-level dispatch
        if msg_type == MsgType.Logon:
            self._logged_in = True
            self._start_heartbeat()
            self.on_logon(msg)
        elif msg_type == MsgType.Logout:
            self._logged_in = False
            self.on_logout(msg)
        elif msg_type == MsgType.Heartbeat:
            pass  # heartbeat acknowledged
        elif msg_type == MsgType.TestRequest:
            # Respond with heartbeat containing the TestReqID
            test_req_id = msg.get_field(Tags.TestReqID) or ""
            hb = FIXMessage.create_heartbeat(
                self.sender_comp_id,
                self.target_comp_id,
                self._next_send_seq(),
                test_req_id,
            )
            self._send_raw(hb)
        elif msg_type == MsgType.ResendRequest:
            self._handle_resend_request(msg)
        elif msg_type == MsgType.ExecutionReport:
            self.on_execution_report(msg)
        elif msg_type == MsgType.OrderCancelReject:
            self.on_order_cancel_reject(msg)

        # Always call the generic handler
        self.on_message(msg)

    def _handle_resend_request(self, msg: FIXMessage) -> None:
        """Handle a ResendRequest by sending a SequenceReset-GapFill.

        A production implementation would replay stored messages; this
        basic implementation sends a gap-fill to the expected sequence.
        """
        begin = int(msg.get_field(Tags.BeginSeqNo) or 1)
        end = int(msg.get_field(Tags.EndSeqNo) or 0)
        logger.warning(
            "ResendRequest %d-%d: sending SequenceReset-GapFill", begin, end
        )
        gap_fill = FIXMessage()
        gap_fill.set_field(Tags.MsgType, MsgType.SequenceReset)
        gap_fill.set_field(Tags.SenderCompID, self.sender_comp_id)
        gap_fill.set_field(Tags.TargetCompID, self.target_comp_id)
        gap_fill.set_field(Tags.MsgSeqNum, begin)
        gap_fill.set_field(Tags.SendingTime, FIXMessage._utc_timestamp())
        gap_fill.set_field(Tags.PossDupFlag, "Y")
        gap_fill.set_field(123, "Y")  # GapFillFlag
        gap_fill.set_field(36, self._send_seq_num)  # NewSeqNo
        self._send_raw(gap_fill)

    # ------------------------------------------------------------------
    # Internal — heartbeat management
    # ------------------------------------------------------------------

    def _start_heartbeat(self) -> None:
        """Start the background heartbeat thread."""
        if (
            self._heartbeat_thread is not None
            and self._heartbeat_thread.is_alive()
        ):
            return
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name="fix-heartbeat"
        )
        self._heartbeat_thread.start()

    def _heartbeat_loop(self) -> None:
        """Periodically send heartbeats if no data has been sent recently."""
        while self._running and self._logged_in:
            elapsed = time.monotonic() - self._last_send_time
            if elapsed >= self.heartbeat_interval:
                try:
                    hb = FIXMessage.create_heartbeat(
                        self.sender_comp_id,
                        self.target_comp_id,
                        self._next_send_seq(),
                    )
                    self._send_raw(hb)
                    logger.debug("Heartbeat sent")
                except Exception as exc:
                    self.on_error(exc)
                    break
            time.sleep(1)

    # ------------------------------------------------------------------
    # Internal — sequence numbers
    # ------------------------------------------------------------------

    def _next_send_seq(self) -> int:
        """Return the next outgoing sequence number and increment."""
        with self._lock:
            seq = self._send_seq_num
            self._send_seq_num += 1
            return seq

    def reset_sequence_numbers(self) -> None:
        """Reset both send and receive sequence numbers to 1."""
        with self._lock:
            self._send_seq_num = 1
            self._recv_seq_num = 1
