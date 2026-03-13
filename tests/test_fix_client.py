"""Tests for FIXClient — session management, sequence numbers, translation."""

import socket
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from fix_protocol.fix_client import FIXClient
from fix_protocol.fix_constants import MsgType, Tags
from fix_protocol.fix_message import FIXMessage
from fix_protocol.fix_translator import FIXTagTranslator


class TestFIXClientInit:
    """Construction and initial state."""

    def test_initial_state(self):
        client = FIXClient("SENDER", "TARGET", "localhost", 9876)
        assert client.sender_comp_id == "SENDER"
        assert client.target_comp_id == "TARGET"
        assert client.host == "localhost"
        assert client.port == 9876
        assert client.heartbeat_interval == 30
        assert not client.is_connected
        assert not client.is_logged_in

    def test_custom_heartbeat(self):
        client = FIXClient("S", "T", "h", 1, heartbeat_interval=60)
        assert client.heartbeat_interval == 60

    def test_custom_translator(self):
        t = FIXTagTranslator()
        client = FIXClient("S", "T", "h", 1, translator=t)
        assert client.translator is t


class TestFIXClientSequenceNumbers:
    """Sequence number management."""

    def test_sequence_starts_at_1(self):
        client = FIXClient("S", "T", "h", 1)
        assert client._send_seq_num == 1

    def test_next_send_seq_increments(self):
        client = FIXClient("S", "T", "h", 1)
        assert client._next_send_seq() == 1
        assert client._next_send_seq() == 2
        assert client._next_send_seq() == 3

    def test_reset_sequence_numbers(self):
        client = FIXClient("S", "T", "h", 1)
        client._next_send_seq()
        client._next_send_seq()
        client.reset_sequence_numbers()
        assert client._send_seq_num == 1
        assert client._recv_seq_num == 1


class TestFIXClientTranslation:
    """Message translation via the client's translator."""

    def test_translate_message(self):
        client = FIXClient("S", "T", "h", 1)
        msg = FIXMessage()
        msg.set_field(35, "D")
        msg.set_field(55, "AAPL")
        msg.set_field(54, "1")

        result = client.translate_message(msg)
        assert "MsgType=NewOrderSingle" in result
        assert "Symbol=AAPL" in result
        assert "Side=Buy" in result

    def test_translate_with_custom_translator(self):
        class Custom(FIXTagTranslator):
            custom_tag_names = {9001: "DarkPoolID"}

        client = FIXClient("S", "T", "h", 1, translator=Custom())
        msg = FIXMessage()
        msg.set_field(9001, "ABC")
        result = client.translate_message(msg)
        assert "DarkPoolID=ABC" in result


class TestFIXClientConnect:
    """Connection lifecycle (mocked socket)."""

    def test_connect_failure_raises(self):
        client = FIXClient("S", "T", "192.0.2.1", 1)  # non-routable
        with pytest.raises(ConnectionError):
            client.connect(timeout=0.5)

    def test_disconnect_when_not_connected(self):
        """disconnect() should be safe even when never connected."""
        client = FIXClient("S", "T", "h", 1)
        client.disconnect()  # should not raise

    @patch("fix_protocol.fix_client.socket.socket")
    def test_connect_success(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock
        mock_sock.recv.side_effect = socket.timeout  # prevent recv loop blocking

        client = FIXClient("S", "T", "localhost", 9876)
        client.connect()

        assert client.is_connected
        mock_sock.connect.assert_called_once_with(("localhost", 9876))

        client.disconnect()
        assert not client.is_connected


class TestFIXClientMessageBuilding:
    """Verify that send_message fills in session fields."""

    @patch("fix_protocol.fix_client.socket.socket")
    def test_send_message_fills_session_fields(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock
        mock_sock.recv.side_effect = socket.timeout

        client = FIXClient("SENDER", "TARGET", "localhost", 9876)
        client.connect()

        msg = FIXMessage()
        msg.set_field(35, "D")
        msg.set_field(55, "TEST")

        client.send_message(msg)

        # Fields should have been populated
        assert msg.get_field(49) == "SENDER"
        assert msg.get_field(56) == "TARGET"
        assert msg.get_field(34) is not None
        assert msg.get_field(52) is not None

        # Should have been sent
        mock_sock.sendall.assert_called_once()

        client.disconnect()


class TestFIXClientMessageHandling:
    """Test internal message routing."""

    def test_handle_logon_response(self):
        client = FIXClient("S", "T", "h", 1)
        client._running = True

        logon = FIXMessage.create_logon("T", "S", 1, 30)
        data = logon.encode()

        # Simulate receiving a logon message
        client._handle_raw_message(data)

        assert client.is_logged_in

    def test_handle_logout(self):
        client = FIXClient("S", "T", "h", 1)
        client._running = True
        client._logged_in = True

        logout = FIXMessage.create_logout("T", "S", 2)
        data = logout.encode()

        client._handle_raw_message(data)
        assert not client.is_logged_in

    def test_handle_test_request_sends_heartbeat(self):
        client = FIXClient("S", "T", "h", 1)
        client._running = True
        client._socket = MagicMock()

        test_req = FIXMessage.create_test_request("T", "S", 3, "TEST123")
        data = test_req.encode()

        client._handle_raw_message(data)

        # A heartbeat should have been sent in response
        client._socket.sendall.assert_called_once()
        sent_data = client._socket.sendall.call_args[0][0]
        sent_text = sent_data.decode("ascii")
        assert "35=0" in sent_text  # MsgType = Heartbeat
        assert "112=TEST123" in sent_text  # echoed TestReqID

    def test_handle_execution_report_callback(self):
        client = FIXClient("S", "T", "h", 1)
        client._running = True
        received = []

        def on_exec(msg):
            received.append(msg)

        client.on_execution_report = on_exec

        exec_rpt = FIXMessage()
        exec_rpt.set_field(35, "8")
        exec_rpt.set_field(49, "T")
        exec_rpt.set_field(56, "S")
        exec_rpt.set_field(34, 4)
        exec_rpt.set_field(37, "ORDER001")
        exec_rpt.set_field(17, "EXEC001")
        exec_rpt.set_field(150, "0")
        exec_rpt.set_field(39, "0")
        exec_rpt.set_field(55, "AAPL")
        exec_rpt.set_field(54, "1")
        exec_rpt.set_field(151, "100")
        exec_rpt.set_field(14, "0")
        exec_rpt.set_field(6, "0")
        data = exec_rpt.encode()

        client._handle_raw_message(data)
        assert len(received) == 1
        assert received[0].get_field(37) == "ORDER001"

    def test_on_message_always_called(self):
        client = FIXClient("S", "T", "h", 1)
        client._running = True
        received = []

        client.on_message = lambda msg: received.append(msg.get_field(35))

        heartbeat = FIXMessage.create_heartbeat("T", "S", 1)
        client._handle_raw_message(heartbeat.encode())

        assert received == ["0"]

    def test_recv_seq_num_updates(self):
        client = FIXClient("S", "T", "h", 1)
        client._running = True
        assert client._recv_seq_num == 1

        msg = FIXMessage.create_heartbeat("T", "S", 5)
        client._handle_raw_message(msg.encode())

        assert client._recv_seq_num == 6  # seq 5 + 1


class TestFIXClientSubclass:
    """Demonstrate subclassing for custom behaviour."""

    def test_subclass_override_hooks(self):
        class MyClient(FIXClient):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.exec_reports = []

            def on_execution_report(self, msg):
                self.exec_reports.append({
                    "order_id": msg.get_field(Tags.OrderID),
                    "exec_type": msg.get_field(Tags.ExecType),
                    "symbol": msg.get_field(Tags.Symbol),
                })

        client = MyClient("S", "T", "h", 1)
        client._running = True

        exec_rpt = FIXMessage()
        exec_rpt.set_field(35, "8")
        exec_rpt.set_field(49, "T")
        exec_rpt.set_field(56, "S")
        exec_rpt.set_field(34, 1)
        exec_rpt.set_field(37, "O1")
        exec_rpt.set_field(17, "E1")
        exec_rpt.set_field(150, "2")
        exec_rpt.set_field(39, "2")
        exec_rpt.set_field(55, "MSFT")
        exec_rpt.set_field(54, "1")
        exec_rpt.set_field(151, "0")
        exec_rpt.set_field(14, "50")
        exec_rpt.set_field(6, "200.50")
        client._handle_raw_message(exec_rpt.encode())

        assert len(client.exec_reports) == 1
        assert client.exec_reports[0]["order_id"] == "O1"
        assert client.exec_reports[0]["exec_type"] == "2"
        assert client.exec_reports[0]["symbol"] == "MSFT"
