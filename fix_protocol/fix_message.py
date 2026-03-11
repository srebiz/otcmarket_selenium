"""
FIX message construction and parsing.

Builds well-formed FIX 4.2 messages with correct BodyLength and CheckSum,
and parses raw FIX byte strings back into structured tag/value pairs.
"""

from __future__ import annotations

import time
from typing import List, Optional, Tuple

#: ASCII SOH (Start of Header) — the standard FIX field delimiter.
SOH = "\x01"


class FIXMessage:
    """Construct and parse FIX 4.2 messages.

    A FIXMessage stores an ordered list of ``(tag, value)`` pairs.
    Session-level header tags (BeginString, BodyLength, CheckSum) are
    computed automatically when the message is serialised via
    :meth:`encode`.

    Example — build a Logon message::

        msg = FIXMessage()
        msg.set_field(35, "A")         # MsgType = Logon
        msg.set_field(49, "SENDER")    # SenderCompID
        msg.set_field(56, "TARGET")    # TargetCompID
        msg.set_field(34, 1)           # MsgSeqNum
        msg.set_field(98, 0)           # EncryptMethod = None
        msg.set_field(108, 30)         # HeartBtInt = 30s
        raw = msg.encode()
    """

    def __init__(self, begin_string: str = "FIX.4.2") -> None:
        self._begin_string = begin_string
        self._fields: List[Tuple[int, str]] = []

    # ------------------------------------------------------------------
    # Field manipulation
    # ------------------------------------------------------------------

    def set_field(self, tag: int, value) -> "FIXMessage":
        """Set a tag/value pair, replacing any existing value for *tag*.

        *value* is converted to ``str`` automatically.  Returns ``self``
        for chaining.
        """
        str_value = str(value)
        # Replace if tag already present
        for i, (t, _) in enumerate(self._fields):
            if t == tag:
                self._fields[i] = (tag, str_value)
                return self
        self._fields.append((tag, str_value))
        return self

    def get_field(self, tag: int) -> Optional[str]:
        """Return the value for *tag*, or ``None`` if not present."""
        for t, v in self._fields:
            if t == tag:
                return v
        return None

    def remove_field(self, tag: int) -> "FIXMessage":
        """Remove the first occurrence of *tag*.  Returns ``self``."""
        self._fields = [(t, v) for t, v in self._fields if t != tag]
        return self

    def to_pairs(self) -> List[Tuple[int, str]]:
        """Return a copy of all ``(tag, value)`` pairs (no header/trailer)."""
        return list(self._fields)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def encode(self) -> bytes:
        """Serialise the message to a FIX wire-format byte string.

        Automatically prepends ``BeginString`` (8) and ``BodyLength`` (9),
        and appends ``CheckSum`` (10).  Tags 8, 9, and 10 in the internal
        field list are ignored during encoding — they are computed fresh.
        """
        # Build body (everything between BodyLength and CheckSum)
        body_parts: list[str] = []
        for tag, value in self._fields:
            if tag in (8, 9, 10):
                continue  # computed automatically
            body_parts.append(f"{tag}={value}{SOH}")
        body = "".join(body_parts)

        # BeginString + BodyLength header
        header = f"8={self._begin_string}{SOH}9={len(body)}{SOH}"

        # CheckSum: sum of all bytes (header + body) mod 256, zero-padded
        raw = header + body
        checksum = sum(ord(c) for c in raw) % 256
        trailer = f"10={checksum:03d}{SOH}"

        return (raw + trailer).encode("ascii")

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @classmethod
    def decode(cls, data: bytes) -> "FIXMessage":
        """Parse a raw FIX byte string into a :class:`FIXMessage`.

        Raises :class:`ValueError` if the data cannot be parsed or the
        checksum does not match.
        """
        text = data.decode("ascii")

        # Split on SOH, filter empty trailing element
        tokens = [t for t in text.split(SOH) if t]

        pairs: list[tuple[int, str]] = []
        begin_string = "FIX.4.2"

        for token in tokens:
            if "=" not in token:
                continue
            tag_str, value = token.split("=", 1)
            tag = int(tag_str)
            if tag == 8:
                begin_string = value
            pairs.append((tag, value))

        msg = cls(begin_string=begin_string)
        for tag, value in pairs:
            if tag in (8, 9, 10):
                continue  # these are recomputed on encode
            msg._fields.append((tag, value))

        # Validate checksum
        cls._validate_checksum(text, pairs)

        return msg

    @staticmethod
    def _validate_checksum(text: str, pairs: list[tuple[int, str]]) -> None:
        """Verify the checksum (tag 10) of a raw FIX message string."""
        # Find expected checksum from the parsed pairs
        expected_cs: Optional[str] = None
        for tag, value in pairs:
            if tag == 10:
                expected_cs = value
                break

        if expected_cs is None:
            return  # no checksum to validate

        # Compute over everything before "10=..."
        cs_marker = f"{SOH}10="
        idx = text.find(cs_marker)
        if idx == -1:
            # CheckSum might be at the very start (unlikely but handle)
            return
        before_cs = text[: idx + 1]  # include the trailing SOH before 10=
        computed = sum(ord(c) for c in before_cs) % 256
        if f"{computed:03d}" != expected_cs:
            raise ValueError(
                f"Checksum mismatch: computed {computed:03d}, "
                f"expected {expected_cs}"
            )

    # ------------------------------------------------------------------
    # Convenience factories
    # ------------------------------------------------------------------

    @classmethod
    def create_logon(
        cls,
        sender: str,
        target: str,
        seq_num: int,
        heartbeat_interval: int = 30,
        *,
        reset_seq: bool = False,
    ) -> "FIXMessage":
        """Build a FIX 4.2 Logon (MsgType=A) message."""
        msg = cls()
        msg.set_field(35, "A")
        msg.set_field(49, sender)
        msg.set_field(56, target)
        msg.set_field(34, seq_num)
        msg.set_field(52, cls._utc_timestamp())
        msg.set_field(98, 0)  # EncryptMethod = None
        msg.set_field(108, heartbeat_interval)
        if reset_seq:
            msg.set_field(141, "Y")
        return msg

    @classmethod
    def create_logout(
        cls, sender: str, target: str, seq_num: int, text: str = ""
    ) -> "FIXMessage":
        """Build a FIX 4.2 Logout (MsgType=5) message."""
        msg = cls()
        msg.set_field(35, "5")
        msg.set_field(49, sender)
        msg.set_field(56, target)
        msg.set_field(34, seq_num)
        msg.set_field(52, cls._utc_timestamp())
        if text:
            msg.set_field(58, text)
        return msg

    @classmethod
    def create_heartbeat(
        cls,
        sender: str,
        target: str,
        seq_num: int,
        test_req_id: str = "",
    ) -> "FIXMessage":
        """Build a FIX 4.2 Heartbeat (MsgType=0) message."""
        msg = cls()
        msg.set_field(35, "0")
        msg.set_field(49, sender)
        msg.set_field(56, target)
        msg.set_field(34, seq_num)
        msg.set_field(52, cls._utc_timestamp())
        if test_req_id:
            msg.set_field(112, test_req_id)
        return msg

    @classmethod
    def create_test_request(
        cls, sender: str, target: str, seq_num: int, test_req_id: str
    ) -> "FIXMessage":
        """Build a FIX 4.2 TestRequest (MsgType=1) message."""
        msg = cls()
        msg.set_field(35, "1")
        msg.set_field(49, sender)
        msg.set_field(56, target)
        msg.set_field(34, seq_num)
        msg.set_field(52, cls._utc_timestamp())
        msg.set_field(112, test_req_id)
        return msg

    @classmethod
    def create_new_order_single(
        cls,
        sender: str,
        target: str,
        seq_num: int,
        cl_ord_id: str,
        symbol: str,
        side: str,
        order_qty: int,
        ord_type: str,
        price: Optional[float] = None,
        *,
        account: str = "",
        currency: str = "",
        time_in_force: str = "0",
        handl_inst: str = "1",
    ) -> "FIXMessage":
        """Build a FIX 4.2 NewOrderSingle (MsgType=D) message.

        Parameters
        ----------
        side : str
            ``"1"`` = Buy, ``"2"`` = Sell (see :class:`fix_constants.Side`).
        ord_type : str
            ``"1"`` = Market, ``"2"`` = Limit (see :class:`fix_constants.OrdType`).
        price : float, optional
            Required for Limit orders.
        """
        msg = cls()
        msg.set_field(35, "D")
        msg.set_field(49, sender)
        msg.set_field(56, target)
        msg.set_field(34, seq_num)
        msg.set_field(52, cls._utc_timestamp())
        msg.set_field(11, cl_ord_id)
        msg.set_field(21, handl_inst)
        msg.set_field(55, symbol)
        msg.set_field(54, side)
        msg.set_field(60, cls._utc_timestamp())
        msg.set_field(38, order_qty)
        msg.set_field(40, ord_type)
        if price is not None:
            msg.set_field(44, f"{price:.2f}")
        msg.set_field(59, time_in_force)
        if account:
            msg.set_field(1, account)
        if currency:
            msg.set_field(15, currency)
        return msg

    @classmethod
    def create_order_cancel_request(
        cls,
        sender: str,
        target: str,
        seq_num: int,
        cl_ord_id: str,
        orig_cl_ord_id: str,
        symbol: str,
        side: str,
        order_qty: int,
    ) -> "FIXMessage":
        """Build a FIX 4.2 OrderCancelRequest (MsgType=F) message."""
        msg = cls()
        msg.set_field(35, "F")
        msg.set_field(49, sender)
        msg.set_field(56, target)
        msg.set_field(34, seq_num)
        msg.set_field(52, cls._utc_timestamp())
        msg.set_field(11, cl_ord_id)
        msg.set_field(41, orig_cl_ord_id)
        msg.set_field(55, symbol)
        msg.set_field(54, side)
        msg.set_field(60, cls._utc_timestamp())
        msg.set_field(38, order_qty)
        return msg

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _utc_timestamp() -> str:
        """Return the current UTC time in FIX timestamp format."""
        return time.strftime("%Y%m%d-%H:%M:%S", time.gmtime())

    def __repr__(self) -> str:
        tag35 = self.get_field(35) or "?"
        return f"<FIXMessage MsgType={tag35} fields={len(self._fields)}>"
