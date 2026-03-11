"""Tests for FIXMessage construction, encoding, decoding, and factories."""

import pytest

from fix_protocol.fix_message import FIXMessage, SOH


class TestFIXMessageFields:
    """Basic field get/set/remove operations."""

    def test_set_and_get_field(self):
        msg = FIXMessage()
        msg.set_field(35, "D")
        assert msg.get_field(35) == "D"

    def test_set_field_converts_to_str(self):
        msg = FIXMessage()
        msg.set_field(38, 100)
        assert msg.get_field(38) == "100"

    def test_set_field_replaces_existing(self):
        msg = FIXMessage()
        msg.set_field(55, "AAPL")
        msg.set_field(55, "GOOG")
        assert msg.get_field(55) == "GOOG"

    def test_get_field_returns_none_for_missing(self):
        msg = FIXMessage()
        assert msg.get_field(999) is None

    def test_remove_field(self):
        msg = FIXMessage()
        msg.set_field(55, "AAPL")
        msg.remove_field(55)
        assert msg.get_field(55) is None

    def test_to_pairs(self):
        msg = FIXMessage()
        msg.set_field(35, "D")
        msg.set_field(55, "AAPL")
        pairs = msg.to_pairs()
        assert (35, "D") in pairs
        assert (55, "AAPL") in pairs

    def test_set_field_chaining(self):
        msg = FIXMessage()
        result = msg.set_field(35, "D").set_field(55, "AAPL").set_field(54, "1")
        assert result is msg
        assert msg.get_field(35) == "D"
        assert msg.get_field(55) == "AAPL"
        assert msg.get_field(54) == "1"


class TestFIXMessageEncode:
    """Encoding to wire format."""

    def test_encode_produces_bytes(self):
        msg = FIXMessage()
        msg.set_field(35, "A")
        msg.set_field(49, "SENDER")
        msg.set_field(56, "TARGET")
        msg.set_field(34, 1)
        data = msg.encode()
        assert isinstance(data, bytes)

    def test_encode_starts_with_begin_string(self):
        msg = FIXMessage()
        msg.set_field(35, "A")
        data = msg.encode().decode("ascii")
        assert data.startswith("8=FIX.4.2" + SOH)

    def test_encode_contains_body_length(self):
        msg = FIXMessage()
        msg.set_field(35, "0")
        data = msg.encode().decode("ascii")
        assert "9=" in data

    def test_encode_ends_with_checksum(self):
        msg = FIXMessage()
        msg.set_field(35, "A")
        data = msg.encode().decode("ascii")
        # CheckSum is last field, format: 10=NNN\x01
        assert data.endswith(SOH)
        parts = data.split(SOH)
        # Last non-empty part should be checksum
        checksum_part = [p for p in parts if p.startswith("10=")]
        assert len(checksum_part) == 1
        cs_value = checksum_part[0].split("=")[1]
        assert len(cs_value) == 3
        assert cs_value.isdigit()

    def test_encode_excludes_manual_tag8_9_10(self):
        """Tags 8, 9, 10 set by user should be ignored — auto-computed."""
        msg = FIXMessage()
        msg.set_field(8, "BAD")
        msg.set_field(9, "999")
        msg.set_field(10, "000")
        msg.set_field(35, "A")
        data = msg.encode().decode("ascii")
        assert "8=FIX.4.2" in data
        assert "8=BAD" not in data

    def test_encode_body_length_is_correct(self):
        msg = FIXMessage()
        msg.set_field(35, "A")
        msg.set_field(49, "SENDER")
        msg.set_field(56, "TARGET")
        data = msg.encode().decode("ascii")

        # Extract body length from encoded message
        tokens = data.split(SOH)
        body_length_str = [t for t in tokens if t.startswith("9=")][0]
        body_length = int(body_length_str.split("=")[1])

        # Body is everything after "8=...\x019=N\x01" and before "10=...\x01"
        begin_end = data.index(SOH) + 1  # after 8=FIX.4.2\x01
        bl_field = body_length_str + SOH
        body_start = data.index(bl_field) + len(bl_field)
        cs_start = data.index(SOH + "10=") + 1  # the SOH before 10=

        actual_body = data[body_start:cs_start]
        assert len(actual_body) == body_length


class TestFIXMessageDecode:
    """Decoding from wire format."""

    def test_roundtrip_encode_decode(self):
        original = FIXMessage()
        original.set_field(35, "D")
        original.set_field(49, "SENDER")
        original.set_field(56, "TARGET")
        original.set_field(34, 1)
        original.set_field(55, "AAPL")

        data = original.encode()
        decoded = FIXMessage.decode(data)

        assert decoded.get_field(35) == "D"
        assert decoded.get_field(49) == "SENDER"
        assert decoded.get_field(56) == "TARGET"
        assert decoded.get_field(55) == "AAPL"

    def test_decode_invalid_checksum_raises(self):
        msg = FIXMessage()
        msg.set_field(35, "A")
        data = msg.encode()
        # Corrupt the checksum
        text = data.decode("ascii")
        text = text.replace("10=", "10=999" + SOH + "10=")
        # This should not match — but let's test with a directly bad checksum
        # Build a message with wrong checksum
        corrupted = text[:-5] + "000" + SOH
        with pytest.raises(ValueError, match="Checksum mismatch"):
            FIXMessage.decode(corrupted.encode("ascii"))

    def test_decode_preserves_begin_string(self):
        msg = FIXMessage(begin_string="FIX.4.4")
        msg.set_field(35, "A")
        data = msg.encode()
        decoded = FIXMessage.decode(data)
        assert decoded._begin_string == "FIX.4.4"


class TestFIXMessageFactories:
    """Factory methods for common message types."""

    def test_create_logon(self):
        msg = FIXMessage.create_logon("SENDER", "TARGET", 1, 30)
        assert msg.get_field(35) == "A"
        assert msg.get_field(49) == "SENDER"
        assert msg.get_field(56) == "TARGET"
        assert msg.get_field(34) == "1"
        assert msg.get_field(98) == "0"
        assert msg.get_field(108) == "30"

    def test_create_logon_with_reset(self):
        msg = FIXMessage.create_logon("S", "T", 1, 30, reset_seq=True)
        assert msg.get_field(141) == "Y"

    def test_create_logout(self):
        msg = FIXMessage.create_logout("SENDER", "TARGET", 2, text="Bye")
        assert msg.get_field(35) == "5"
        assert msg.get_field(58) == "Bye"

    def test_create_logout_no_text(self):
        msg = FIXMessage.create_logout("S", "T", 1)
        assert msg.get_field(35) == "5"
        assert msg.get_field(58) is None

    def test_create_heartbeat(self):
        msg = FIXMessage.create_heartbeat("S", "T", 3)
        assert msg.get_field(35) == "0"
        assert msg.get_field(112) is None

    def test_create_heartbeat_with_test_req_id(self):
        msg = FIXMessage.create_heartbeat("S", "T", 3, "TEST123")
        assert msg.get_field(35) == "0"
        assert msg.get_field(112) == "TEST123"

    def test_create_test_request(self):
        msg = FIXMessage.create_test_request("S", "T", 4, "REQ1")
        assert msg.get_field(35) == "1"
        assert msg.get_field(112) == "REQ1"

    def test_create_new_order_single_market(self):
        msg = FIXMessage.create_new_order_single(
            "SENDER", "TARGET", 5, "ORD001", "AAPL", "1", 100, "1"
        )
        assert msg.get_field(35) == "D"
        assert msg.get_field(11) == "ORD001"
        assert msg.get_field(55) == "AAPL"
        assert msg.get_field(54) == "1"
        assert msg.get_field(38) == "100"
        assert msg.get_field(40) == "1"
        assert msg.get_field(44) is None  # no price for market orders

    def test_create_new_order_single_limit(self):
        msg = FIXMessage.create_new_order_single(
            "SENDER", "TARGET", 5, "ORD002", "GOOG", "2", 50, "2",
            price=150.25,
        )
        assert msg.get_field(35) == "D"
        assert msg.get_field(40) == "2"
        assert msg.get_field(44) == "150.25"

    def test_create_new_order_single_with_optionals(self):
        msg = FIXMessage.create_new_order_single(
            "S", "T", 1, "O1", "SYM", "1", 10, "2", 99.99,
            account="ACC1", currency="USD", time_in_force="1",
        )
        assert msg.get_field(1) == "ACC1"
        assert msg.get_field(15) == "USD"
        assert msg.get_field(59) == "1"

    def test_create_order_cancel_request(self):
        msg = FIXMessage.create_order_cancel_request(
            "S", "T", 6, "CANCEL1", "ORD001", "AAPL", "1", 100
        )
        assert msg.get_field(35) == "F"
        assert msg.get_field(11) == "CANCEL1"
        assert msg.get_field(41) == "ORD001"


class TestFIXMessageRepr:
    def test_repr(self):
        msg = FIXMessage()
        msg.set_field(35, "D")
        msg.set_field(55, "AAPL")
        r = repr(msg)
        assert "MsgType=D" in r
        assert "fields=2" in r
