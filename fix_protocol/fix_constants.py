"""
FIX 4.2 protocol constants — tag numbers, message types, and enumerated values.

This module provides human-readable names for the most commonly used FIX 4.2
tags and field values used in OTC market trading workflows.
"""


class Tags:
    """Numeric FIX tag identifiers (FIX 4.2)."""

    # Session-level tags
    BeginString = 8
    BodyLength = 9
    MsgType = 35
    SenderCompID = 49
    TargetCompID = 56
    MsgSeqNum = 34
    SendingTime = 52
    CheckSum = 10
    PossDupFlag = 43
    PossResend = 97
    OrigSendingTime = 122

    # Logon / session tags
    EncryptMethod = 98
    HeartBtInt = 108
    ResetSeqNumFlag = 141
    TestReqID = 112
    BeginSeqNo = 7
    EndSeqNo = 16

    # Order-related tags
    ClOrdID = 11
    OrderID = 37
    ExecID = 17
    ExecTransType = 20
    ExecType = 150
    OrdStatus = 39
    Symbol = 55
    SecurityID = 48
    SecurityIDSource = 22
    Side = 54
    OrderQty = 38
    OrdType = 40
    Price = 44
    StopPx = 99
    Currency = 15
    TimeInForce = 59
    ExpireTime = 126
    TransactTime = 60
    Account = 1
    HandlInst = 21
    Text = 58

    # Execution report tags
    LastShares = 32
    LastPx = 31
    LeavesQty = 151
    CumQty = 14
    AvgPx = 6

    # Market data tags
    MDReqID = 262
    SubscriptionRequestType = 263
    MarketDepth = 264
    MDUpdateType = 265
    NoMDEntryTypes = 267
    MDEntryType = 269
    NoMDEntries = 268
    MDEntryPx = 270
    MDEntrySize = 271

    # Identification
    SecurityExchange = 207
    IDSource = 22


class MsgType:
    """FIX message type values (tag 35)."""

    Heartbeat = "0"
    TestRequest = "1"
    ResendRequest = "2"
    Reject = "3"
    SequenceReset = "4"
    Logout = "5"
    Logon = "A"
    NewOrderSingle = "D"
    OrderCancelRequest = "F"
    OrderCancelReplaceRequest = "G"
    OrderStatusRequest = "H"
    ExecutionReport = "8"
    OrderCancelReject = "9"
    MarketDataRequest = "V"
    MarketDataSnapshotFullRefresh = "W"
    MarketDataIncrementalRefresh = "X"


class OrdType:
    """Order type values (tag 40)."""

    Market = "1"
    Limit = "2"
    Stop = "3"
    StopLimit = "4"


class Side:
    """Order side values (tag 54)."""

    Buy = "1"
    Sell = "2"
    BuyMinus = "3"
    SellPlus = "4"
    SellShort = "5"
    SellShortExempt = "6"


class TimeInForce:
    """Time-in-force values (tag 59)."""

    Day = "0"
    GoodTillCancel = "1"
    AtTheOpening = "2"
    ImmediateOrCancel = "3"
    FillOrKill = "4"
    GoodTillDate = "6"


class ExecType:
    """Execution type values (tag 150)."""

    New = "0"
    PartialFill = "1"
    Fill = "2"
    DoneForDay = "3"
    Canceled = "4"
    Replace = "5"
    PendingCancel = "6"
    Stopped = "7"
    Rejected = "8"
    Suspended = "9"
    PendingNew = "A"
    Calculated = "B"
    Expired = "C"
    PendingReplace = "E"


class OrdStatus:
    """Order status values (tag 39)."""

    New = "0"
    PartiallyFilled = "1"
    Filled = "2"
    DoneForDay = "3"
    Canceled = "4"
    Replaced = "5"
    PendingCancel = "6"
    Stopped = "7"
    Rejected = "8"
    Suspended = "9"
    PendingNew = "A"
    Calculated = "B"
    Expired = "C"
    PendingReplace = "E"


class HandlInst:
    """Handling instruction values (tag 21)."""

    AutomatedNoIntervention = "1"
    AutomatedIntervention = "2"
    Manual = "3"
