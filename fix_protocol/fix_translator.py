"""
FIX tag-to-English translator.

Maps numeric FIX tags to human-readable field names and translates
enumerated values to their English descriptions.  Designed for
subclassing so client code can add proprietary or custom tags.
"""

from __future__ import annotations

from typing import Dict, Optional


class FIXTagTranslator:
    """Translate FIX numeric tags and enumerated values to readable English.

    Override ``custom_tag_names`` or ``custom_value_names`` in a subclass
    to add proprietary tags or venue-specific value mappings.

    Example::

        class MyTranslator(FIXTagTranslator):
            custom_tag_names = {9001: "VenueOrderID", 9002: "VenueStatus"}
            custom_value_names = {9002: {"A": "Active", "I": "Inactive"}}
    """

    # ------------------------------------------------------------------
    # Tag number → human-readable name  (FIX 4.2 common fields)
    # ------------------------------------------------------------------
    TAG_NAMES: Dict[int, str] = {
        # Session-level
        8: "BeginString",
        9: "BodyLength",
        10: "CheckSum",
        34: "MsgSeqNum",
        35: "MsgType",
        43: "PossDupFlag",
        49: "SenderCompID",
        52: "SendingTime",
        56: "TargetCompID",
        97: "PossResend",
        98: "EncryptMethod",
        108: "HeartBtInt",
        112: "TestReqID",
        122: "OrigSendingTime",
        141: "ResetSeqNumFlag",
        7: "BeginSeqNo",
        16: "EndSeqNo",
        # Order / execution
        1: "Account",
        6: "AvgPx",
        11: "ClOrdID",
        14: "CumQty",
        15: "Currency",
        17: "ExecID",
        20: "ExecTransType",
        21: "HandlInst",
        31: "LastPx",
        32: "LastShares",
        37: "OrderID",
        38: "OrderQty",
        39: "OrdStatus",
        40: "OrdType",
        44: "Price",
        48: "SecurityID",
        22: "SecurityIDSource",
        54: "Side",
        55: "Symbol",
        58: "Text",
        59: "TimeInForce",
        60: "TransactTime",
        99: "StopPx",
        126: "ExpireTime",
        150: "ExecType",
        151: "LeavesQty",
        # Market data
        207: "SecurityExchange",
        262: "MDReqID",
        263: "SubscriptionRequestType",
        264: "MarketDepth",
        265: "MDUpdateType",
        267: "NoMDEntryTypes",
        268: "NoMDEntries",
        269: "MDEntryType",
        270: "MDEntryPx",
        271: "MDEntrySize",
    }

    # ------------------------------------------------------------------
    # (tag, raw_value) → human-readable value  (selected enumerations)
    # ------------------------------------------------------------------
    VALUE_NAMES: Dict[int, Dict[str, str]] = {
        35: {  # MsgType
            "0": "Heartbeat",
            "1": "TestRequest",
            "2": "ResendRequest",
            "3": "Reject",
            "4": "SequenceReset",
            "5": "Logout",
            "A": "Logon",
            "D": "NewOrderSingle",
            "F": "OrderCancelRequest",
            "G": "OrderCancelReplaceRequest",
            "H": "OrderStatusRequest",
            "8": "ExecutionReport",
            "9": "OrderCancelReject",
            "V": "MarketDataRequest",
            "W": "MarketDataSnapshotFullRefresh",
            "X": "MarketDataIncrementalRefresh",
        },
        40: {  # OrdType
            "1": "Market",
            "2": "Limit",
            "3": "Stop",
            "4": "StopLimit",
        },
        54: {  # Side
            "1": "Buy",
            "2": "Sell",
            "3": "BuyMinus",
            "4": "SellPlus",
            "5": "SellShort",
            "6": "SellShortExempt",
        },
        59: {  # TimeInForce
            "0": "Day",
            "1": "GoodTillCancel",
            "2": "AtTheOpening",
            "3": "ImmediateOrCancel",
            "4": "FillOrKill",
            "6": "GoodTillDate",
        },
        150: {  # ExecType
            "0": "New",
            "1": "PartialFill",
            "2": "Fill",
            "3": "DoneForDay",
            "4": "Canceled",
            "5": "Replace",
            "6": "PendingCancel",
            "7": "Stopped",
            "8": "Rejected",
            "9": "Suspended",
            "A": "PendingNew",
            "B": "Calculated",
            "C": "Expired",
            "E": "PendingReplace",
        },
        39: {  # OrdStatus
            "0": "New",
            "1": "PartiallyFilled",
            "2": "Filled",
            "3": "DoneForDay",
            "4": "Canceled",
            "5": "Replaced",
            "6": "PendingCancel",
            "7": "Stopped",
            "8": "Rejected",
            "9": "Suspended",
            "A": "PendingNew",
            "B": "Calculated",
            "C": "Expired",
            "E": "PendingReplace",
        },
        21: {  # HandlInst
            "1": "AutomatedNoIntervention",
            "2": "AutomatedIntervention",
            "3": "Manual",
        },
    }

    # Subclass hooks — merge into the class-level dicts at lookup time.
    custom_tag_names: Dict[int, str] = {}
    custom_value_names: Dict[int, Dict[str, str]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def translate_tag(self, tag: int) -> str:
        """Return the human-readable name for a numeric FIX tag.

        Falls back to ``"Tag<N>"`` if the tag is not in the dictionary.
        """
        name = self.custom_tag_names.get(tag) or self.TAG_NAMES.get(tag)
        return name if name else f"Tag{tag}"

    def translate_value(self, tag: int, value: str) -> str:
        """Return the human-readable value for an enumerated FIX field.

        If the tag/value pair is not in the dictionary the raw *value* is
        returned unchanged.
        """
        custom = self.custom_value_names.get(tag, {})
        if value in custom:
            return custom[value]
        builtin = self.VALUE_NAMES.get(tag, {})
        return builtin.get(value, value)

    def translate_pair(self, tag: int, value: str) -> str:
        """Return ``"TagName=ReadableValue"`` for a single tag/value pair."""
        return f"{self.translate_tag(tag)}={self.translate_value(tag, value)}"

    def translate_message(self, pairs: list[tuple[int, str]]) -> list[str]:
        """Translate a full list of ``(tag, value)`` pairs to readable strings.

        Parameters
        ----------
        pairs:
            Iterable of ``(tag_number, raw_value)`` tuples — the format
            returned by ``FIXMessage.to_pairs()``.

        Returns
        -------
        list[str]
            Each element is ``"TagName=ReadableValue"``.
        """
        return [self.translate_pair(tag, value) for tag, value in pairs]
