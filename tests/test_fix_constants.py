"""Tests for FIX constants module."""

from fix_protocol.fix_constants import (
    ExecType,
    HandlInst,
    MsgType,
    OrdStatus,
    OrdType,
    Side,
    Tags,
    TimeInForce,
)


class TestTags:
    """Verify key tag values match the FIX 4.2 spec."""

    def test_session_tags(self):
        assert Tags.BeginString == 8
        assert Tags.BodyLength == 9
        assert Tags.MsgType == 35
        assert Tags.SenderCompID == 49
        assert Tags.TargetCompID == 56
        assert Tags.MsgSeqNum == 34
        assert Tags.SendingTime == 52
        assert Tags.CheckSum == 10

    def test_order_tags(self):
        assert Tags.ClOrdID == 11
        assert Tags.OrderID == 37
        assert Tags.Symbol == 55
        assert Tags.Side == 54
        assert Tags.OrderQty == 38
        assert Tags.OrdType == 40
        assert Tags.Price == 44

    def test_execution_tags(self):
        assert Tags.ExecID == 17
        assert Tags.ExecType == 150
        assert Tags.OrdStatus == 39
        assert Tags.LeavesQty == 151
        assert Tags.CumQty == 14
        assert Tags.AvgPx == 6


class TestMsgType:
    def test_session_message_types(self):
        assert MsgType.Heartbeat == "0"
        assert MsgType.TestRequest == "1"
        assert MsgType.Logon == "A"
        assert MsgType.Logout == "5"

    def test_order_message_types(self):
        assert MsgType.NewOrderSingle == "D"
        assert MsgType.OrderCancelRequest == "F"
        assert MsgType.ExecutionReport == "8"


class TestOrdType:
    def test_values(self):
        assert OrdType.Market == "1"
        assert OrdType.Limit == "2"
        assert OrdType.Stop == "3"
        assert OrdType.StopLimit == "4"


class TestSide:
    def test_values(self):
        assert Side.Buy == "1"
        assert Side.Sell == "2"
        assert Side.SellShort == "5"


class TestExecType:
    def test_values(self):
        assert ExecType.New == "0"
        assert ExecType.Fill == "2"
        assert ExecType.Canceled == "4"
        assert ExecType.Rejected == "8"


class TestOrdStatus:
    def test_values(self):
        assert OrdStatus.New == "0"
        assert OrdStatus.Filled == "2"
        assert OrdStatus.Canceled == "4"


class TestTimeInForce:
    def test_values(self):
        assert TimeInForce.Day == "0"
        assert TimeInForce.GoodTillCancel == "1"
        assert TimeInForce.FillOrKill == "4"


class TestHandlInst:
    def test_values(self):
        assert HandlInst.AutomatedNoIntervention == "1"
        assert HandlInst.Manual == "3"
