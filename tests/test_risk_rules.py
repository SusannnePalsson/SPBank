import pandas as pd
from risk_rules import score_and_flag, RiskConfig

def _base(now):
    return [
        {
            "transaction_id": f"T{i}",
            "timestamp": (now + pd.Timedelta(minutes=i)).isoformat(),
            "amount": 100.0,
            "currency": "SEK",
            "from_account": "A",
            "to_account": "B",
            "sender_country": "Sweden",
            "receiver_country": "Sweden",
            "notes": ""
        } for i in range(3)
    ]

def test_structuring_band_triggers():
    now = pd.Timestamp.now(tz="UTC")
    rows = _base(now)
    rows.append({**rows[-1], "transaction_id":"TS", "amount": 9600.0})  # inom 9500–9999.99
    df = pd.DataFrame(rows)
    cfg = RiskConfig(structuring_by_currency={"SEK":(9500, 9999.99)}, high_amount_p=0.99, crossborder_p=0.99)
    flagged = score_and_flag(df, cfg)
    assert (flagged["transaction_id"]=="TS").any()
    assert flagged.loc[flagged["transaction_id"]=="TS","reason"].str.contains("Structuring band 9500–9999.99 SEK").any()

def test_velocity_rule_triggers():
    now = pd.Timestamp.now(tz="UTC")
    rows = []
    for i in range(21):  # 21 tx inom 24h
        rows.append({
            "transaction_id": f"V{i}",
            "timestamp": (now + pd.Timedelta(minutes=i)).isoformat(),
            "amount": 1.0,
            "currency": "SEK",
            "from_account": "X",
            "to_account": "Y",
            "sender_country": "Sweden",
            "receiver_country": "Sweden",
            "notes":"",
        })
    df = pd.DataFrame(rows)
    cfg = RiskConfig(velocity_window_hours=24, velocity_min_tx=20, high_amount_p=0.999, crossborder_p=0.999)
    flagged = score_and_flag(df, cfg)
    assert any("High velocity ≥ 20 tx/24h" in r for r in flagged["reason"].unique())

def test_pingpong_rule_triggers():
    now = pd.Timestamp.now(tz="UTC")
    df = pd.DataFrame([
        {"transaction_id":"P1","timestamp": now.isoformat(), "amount":10,"currency":"SEK","from_account":"A","to_account":"B","sender_country":"SE","receiver_country":"SE","notes":""},
        {"transaction_id":"P2","timestamp": (now + pd.Timedelta(days=1)).isoformat(), "amount":11,"currency":"SEK","from_account":"B","to_account":"A","sender_country":"SE","receiver_country":"SE","notes":""},
    ])
    cfg = RiskConfig(pingpong_days=7, high_amount_p=0.999, crossborder_p=0.999)
    flagged = score_and_flag(df, cfg)
    assert any("Ping-pong (retur inom 7d)" in r for r in flagged["reason"].unique())

def test_crossborder_requires_high_amount_when_configured():
    now = pd.Timestamp.now(tz="UTC")
    df = pd.DataFrame([
        {"transaction_id":"C1","timestamp": now.isoformat(), "amount":100,"currency":"SEK","from_account":"A","to_account":"B","sender_country":"SE","receiver_country":"NO","notes":""},
        {"transaction_id":"C2","timestamp": (now + pd.Timedelta(minutes=1)).isoformat(), "amount":100000,"currency":"SEK","from_account":"A","to_account":"B","sender_country":"SE","receiver_country":"NO","notes":""},
    ])
    cfg = RiskConfig(require_high_for_crossborder=True, high_amount_p=0.9, crossborder_p=0.9)
    flagged = score_and_flag(df, cfg)
    assert "C1" not in set(flagged["transaction_id"])
    assert "C2" in set(flagged["transaction_id"])

def test_new_counterparty_plus_high_amount():
    now = pd.Timestamp.now(tz="UTC")
    df = pd.DataFrame([
        {"transaction_id":"N1","timestamp": now.isoformat(), "amount":100000,"currency":"SEK","from_account":"A","to_account":"Z","sender_country":"SE","receiver_country":"SE","notes":""},
    ])
    cfg = RiskConfig(new_counterparty_days=14, require_high_for_new_counterparty=True, high_amount_p=0.5, crossborder_p=0.99)
    flagged = score_and_flag(df, cfg)
    assert "N1" in set(flagged["transaction_id"])
    assert any("New counterparty" in r for r in flagged["reason"].unique())