"""Tests for FIXTagTranslator."""

from fix_protocol.fix_translator import FIXTagTranslator


class TestTranslateTag:
    """Tag number → human-readable name."""

    def test_known_tag(self):
        t = FIXTagTranslator()
        assert t.translate_tag(35) == "MsgType"
        assert t.translate_tag(49) == "SenderCompID"
        assert t.translate_tag(55) == "Symbol"

    def test_unknown_tag_fallback(self):
        t = FIXTagTranslator()
        assert t.translate_tag(99999) == "Tag99999"

    def test_custom_tag_in_subclass(self):
        class Custom(FIXTagTranslator):
            custom_tag_names = {9001: "VenueOrderID"}

        t = Custom()
        assert t.translate_tag(9001) == "VenueOrderID"

    def test_custom_tag_overrides_builtin(self):
        class Custom(FIXTagTranslator):
            custom_tag_names = {55: "Ticker"}

        t = Custom()
        assert t.translate_tag(55) == "Ticker"


class TestTranslateValue:
    """Enumerated value → human-readable string."""

    def test_known_enum(self):
        t = FIXTagTranslator()
        assert t.translate_value(35, "A") == "Logon"
        assert t.translate_value(35, "D") == "NewOrderSingle"
        assert t.translate_value(54, "1") == "Buy"
        assert t.translate_value(54, "2") == "Sell"

    def test_unknown_value_returns_raw(self):
        t = FIXTagTranslator()
        assert t.translate_value(35, "ZZZ") == "ZZZ"

    def test_unknown_tag_returns_raw_value(self):
        t = FIXTagTranslator()
        assert t.translate_value(99999, "abc") == "abc"

    def test_custom_value_in_subclass(self):
        class Custom(FIXTagTranslator):
            custom_value_names = {9002: {"A": "Active", "I": "Inactive"}}

        t = Custom()
        assert t.translate_value(9002, "A") == "Active"
        assert t.translate_value(9002, "I") == "Inactive"

    def test_custom_value_overrides_builtin(self):
        class Custom(FIXTagTranslator):
            custom_value_names = {54: {"1": "Long"}}

        t = Custom()
        assert t.translate_value(54, "1") == "Long"
        # Non-overridden values still work
        assert t.translate_value(54, "2") == "Sell"


class TestTranslatePair:
    def test_translate_pair_known(self):
        t = FIXTagTranslator()
        assert t.translate_pair(35, "D") == "MsgType=NewOrderSingle"
        assert t.translate_pair(55, "AAPL") == "Symbol=AAPL"

    def test_translate_pair_unknown(self):
        t = FIXTagTranslator()
        assert t.translate_pair(99999, "X") == "Tag99999=X"


class TestTranslateMessage:
    def test_translate_message(self):
        t = FIXTagTranslator()
        pairs = [(35, "D"), (49, "SENDER"), (55, "GOOG"), (54, "1"), (38, "100")]
        result = t.translate_message(pairs)
        assert result == [
            "MsgType=NewOrderSingle",
            "SenderCompID=SENDER",
            "Symbol=GOOG",
            "Side=Buy",
            "OrderQty=100",
        ]

    def test_translate_empty_message(self):
        t = FIXTagTranslator()
        assert t.translate_message([]) == []

    def test_translate_message_with_custom_subclass(self):
        class OTCTranslator(FIXTagTranslator):
            custom_tag_names = {9001: "DarkPoolID"}
            custom_value_names = {9001: {"1": "PoolAlpha", "2": "PoolBeta"}}

        t = OTCTranslator()
        pairs = [(35, "D"), (9001, "1")]
        result = t.translate_message(pairs)
        assert result == ["MsgType=NewOrderSingle", "DarkPoolID=PoolAlpha"]


class TestAllBuiltinMappings:
    """Verify comprehensive coverage of common FIX fields."""

    def test_session_tags_present(self):
        t = FIXTagTranslator()
        session_tags = {8, 9, 10, 34, 35, 49, 52, 56, 98, 108, 112, 141}
        for tag in session_tags:
            name = t.translate_tag(tag)
            assert not name.startswith("Tag"), f"Tag {tag} not mapped"

    def test_order_tags_present(self):
        t = FIXTagTranslator()
        order_tags = {1, 11, 14, 15, 17, 21, 31, 32, 37, 38, 39, 40, 44, 54, 55, 59, 60, 150, 151}
        for tag in order_tags:
            name = t.translate_tag(tag)
            assert not name.startswith("Tag"), f"Tag {tag} not mapped"

    def test_msgtype_values_covered(self):
        t = FIXTagTranslator()
        msg_types = ["0", "1", "2", "3", "4", "5", "A", "D", "F", "G", "H", "8", "9"]
        for mt in msg_types:
            name = t.translate_value(35, mt)
            assert name != mt, f"MsgType {mt} not mapped"
