# risk_rules.py
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, Tuple, Iterable, Optional
import pandas as pd
import numpy as np


@dataclass
class RiskConfig:
    # Grundtrösklar (percentiler per valuta)
    high_amount_p: float = 0.98
    crossborder_p: float = 0.98

    # Structuring-intervall per valuta (None => hoppa regeln eller använd default nedan)
    structuring_by_currency: Dict[str, Tuple[float, float]] | None = None

    # Nyckelord i notes
    keyword_list: Iterable[str] = ("crypto", "urgent")

    # Kombinationslogik (för att minska brus)
    require_high_for_keyword: bool = True
    require_high_for_crossborder: bool = True
    exclude_structuring_from_crossborder: bool = True

    # Avancerade regler
    # Velocity
    velocity_window_hours: int = 24
    velocity_min_tx: int = 20  # antal tx inom fönstret som triggar flagg

    # Ping-pong (rundgång mellan två konton)
    pingpong_days: int = 7
    pingpong_min_pairs: int = 1  # hur många “returer” som krävs

    # Ny motpart (första gången A->B inom Y dagar)
    new_counterparty_days: int = 14
    require_high_for_new_counterparty: bool = True

    # Failsafe (valfritt): cap per reason (None = ingen cap)
    cap_per_reason: Optional[int] = None  # t.ex. 3000


# ---------------- Hjälpfunktioner ----------------

def _ensure_numeric_amount(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["amount"] = pd.to_numeric(out["amount"], errors="coerce")
    out = out[out["amount"].notna()]
    return out


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalisera till följande kolumner om möjligt:
      transaction_id, amount, currency, notes,
      from_account, to_account, sender_country, receiver_country, timestamp (datetime64[ns, UTC] eller NaT)
    Saknas något hoppar relaterade regler över automatiskt.
    """
    out = df.copy()

    # transaction_id/id
    if "transaction_id" not in out.columns and "id" in out.columns:
        out = out.rename(columns={"id": "transaction_id"})
    if "transaction_id" not in out.columns:
        raise ValueError("Saknar kolumn 'transaction_id' eller 'id'.")

    # from/to (försök flera varianter)
    col_from_candidates = ["from_account", "sender_account_id", "sender_account", "sender_account_number"]
    col_to_candidates   = ["to_account", "receiver_account_id", "receiver_account", "receiver_account_number"]
    from_col = next((c for c in col_from_candidates if c in out.columns), None)
    to_col   = next((c for c in col_to_candidates if c in out.columns), None)
    out["from_account"] = out[from_col] if from_col else ""
    out["to_account"]   = out[to_col]   if to_col   else ""

    # countries
    out["sender_country"]   = out["sender_country"]   if "sender_country" in out.columns   else ""
    out["receiver_country"] = out["receiver_country"] if "receiver_country" in out.columns else ""

    # notes
    out["notes"] = out["notes"] if "notes" in out.columns else ""
    out["notes"] = out["notes"].fillna("")

    # currency
    if "currency" not in out.columns:
        raise ValueError("Saknar kolumn 'currency'.")

    # timestamp → datetime (om finns)
    if "timestamp" in out.columns:
        out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce", utc=True)
    else:
        out["timestamp"] = pd.NaT  # gör kolumnen åtminstone närvarande

    return out


def _percentiles_per_currency(df: pd.DataFrame, p: float) -> dict:
    if df.empty:
        return {}
    return df.groupby("currency")["amount"].quantile(p).to_dict()


# ---------------- Regelmasker (enkla) ----------------

def _rule_high_amount(df: pd.DataFrame, p: float) -> pd.Series:
    thr = _percentiles_per_currency(df, p)
    if not thr:
        return pd.Series(False, index=df.index)
    return df.apply(lambda r: r["amount"] >= thr.get(r["currency"], np.inf), axis=1)


def _rule_crossborder_high(df: pd.DataFrame, p: float) -> pd.Series:
    thr = _percentiles_per_currency(df, p)
    cross = df["sender_country"].astype(str).ne(df["receiver_country"].astype(str))
    return cross & df.apply(lambda r: r["amount"] >= thr.get(r["currency"], np.inf), axis=1)


def _rule_structuring(df: pd.DataFrame, ranges: Dict[str, Tuple[float, float]] | None) -> pd.Series:
    if not ranges:
        return pd.Series(False, index=df.index)

    def in_band(r):
        band = ranges.get(str(r["currency"]))
        if not band:
            return False
        lo, hi = band
        return (r["amount"] >= lo) and (r["amount"] <= hi)

    return df.apply(in_band, axis=1)


def _rule_keyword(df: pd.DataFrame, keywords: Iterable[str]) -> pd.Series:
    if not keywords:
        return pd.Series(False, index=df.index)
    pattern = re.compile("|".join(re.escape(w) for w in keywords), flags=re.IGNORECASE)
    return df["notes"].str.contains(pattern, na=False)


# ---------------- Avancerade regler ----------------

def _rule_velocity(df: pd.DataFrame, hours: int, min_tx: int) -> pd.Series:
    """
    Flagga om ett konto (from_account) gör minst 'min_tx' transaktioner
    inom ett glidande fönster på 'hours' timmar.
    Kräver giltig 'timestamp' (timezone-aware) och 'from_account'.
    """
    if "from_account" not in df.columns or df["timestamp"].isna().all():
        return pd.Series(False, index=df.index)

    work = df[["from_account", "timestamp"]].copy()
    work = work.dropna(subset=["from_account", "timestamp"]).sort_values(["from_account", "timestamp"])
    flags = pd.Series(False, index=df.index)

    for acc, g in work.groupby("from_account", sort=False):
        g = g.set_index("timestamp").sort_index()
        ones = pd.Series(1, index=g.index)
        # Viktigt: litet 'h' (framtidssäkert)
        cnt = ones.rolling(f"{hours}h").sum().astype(int)
        hit_idx = g.iloc[(cnt >= min_tx).values].index
        mask = (df["from_account"] == acc) & (df["timestamp"].isin(hit_idx))
        flags.loc[mask] = True

    return flags


def _rule_pingpong(df: pd.DataFrame, days: int, min_pairs: int) -> pd.Series:
    """
    Flaggar transaktioner där det finns en retur (B->A) inom 'days' dagar
    för den aktuella transaktionen (A->B).
    """
    if df["timestamp"].isna().all():
        return pd.Series(False, index=df.index)
    if "from_account" not in df.columns or "to_account" not in df.columns:
        return pd.Series(False, index=df.index)

    # A->B
    left = (
        df[["from_account", "to_account", "timestamp"]]
        .dropna()
        .rename(columns={"from_account": "A", "to_account": "B"})
        .sort_values("timestamp")
    )

    # B->A (returer). Lägg till markörkolumn som överlever merge_asof.
    right = (
        df[["from_account", "to_account", "timestamp"]]
        .dropna()
        .rename(columns={"from_account": "B", "to_account": "A"})
        .sort_values("timestamp")
        .assign(had_rev=1)
    )

    # merge_asof på tid och par-nycklar
    m = pd.merge_asof(
        left,
        right,
        on="timestamp",
        by=["A", "B"],
        direction="backward",
        tolerance=pd.Timedelta(days=days),
        suffixes=("", "_rev"),
    )

    # träff om markör finns (NaN => ingen träff)
    has_rev = m["had_rev"].notna()

    # Mappa tillbaka till ursprungsrader i df
    idx = pd.Series(False, index=df.index)
    if has_rev.any():
        matched = m.loc[has_rev, ["A", "B", "timestamp"]]
        key_df = (df["from_account"].astype(str) + "|" +
                  df["to_account"].astype(str) + "|" +
                  df["timestamp"].astype(str))
        key_m  = (matched["A"].astype(str) + "|" +
                  matched["B"].astype(str) + "|" +
                  matched["timestamp"].astype(str))
        idx.loc[key_df.isin(set(key_m))] = True

    # Kräver fler än 1 retur? Filtrera bort par som inte når gränsen.
    if min_pairs > 1 and idx.any():
        pair_series = m.loc[has_rev, ["A", "B"]].astype(str).apply(tuple, axis=1)
        counts = pair_series.value_counts()
        poor_pairs = {pair for pair, cnt in counts.items() if cnt < min_pairs}
        if poor_pairs:
            kill_mask = (df["from_account"].astype(str) + "|" +
                         df["to_account"].astype(str)).apply(
                lambda s: tuple(s.split("|")) in poor_pairs
            )
            idx = idx & (~kill_mask)

    return idx

from pandas.api.types import is_datetime64_any_dtype

def _rule_new_counterparty(df: pd.DataFrame, days: int, require_high: bool, m_high: pd.Series) -> pd.Series:
    if df.empty:
        return pd.Series(False, index=df.index)

    # ✅ Korrekt dtype-koll även för timezone-aware timestamps
    if not is_datetime64_any_dtype(df["timestamp"]):
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    d = df[["from_account", "to_account", "timestamp"]].copy()
    d = d.sort_values("timestamp").copy()
    d["timestamp_prev"] = d.groupby(["from_account", "to_account"])["timestamp"].shift(1)
    d = d.reindex(df.index)

    is_first = d["timestamp_prev"].isna()
    gap_days = (d["timestamp"] - d["timestamp_prev"]).dt.total_seconds() / 86400.0
    is_new_after_gap = gap_days >= float(days)
    is_new_after_gap = is_new_after_gap.fillna(False)

    mask = is_first | is_new_after_gap
    if require_high:
        mask = mask & m_high

    return mask.fillna(False)


# ---------------- Huvudfunktion ----------------

def score_and_flag(trans: pd.DataFrame, cfg: RiskConfig) -> pd.DataFrame:
    """Returnerar DF: transaction_id, reason, flagged_date, amount"""

    # Defaults för structuring-band (smala → mindre brus)
    if cfg.structuring_by_currency is None:
        cfg.structuring_by_currency = {
            "SEK": (9500, 9999.99),
            "EUR": (950, 999.99),
            "USD": (950, 999.99),
        }

    df = _normalize_columns(trans)
    df = _ensure_numeric_amount(df)

    # Basmasker
    m_high     = _rule_high_amount(df, cfg.high_amount_p)
    m_xborder  = _rule_crossborder_high(df, cfg.crossborder_p)
    m_struct   = _rule_structuring(df, cfg.structuring_by_currency)
    m_keyword  = _rule_keyword(df, cfg.keyword_list)

    # Kombinationslogik (enkel brusreduktion)
    if cfg.require_high_for_keyword:
        m_keyword = m_keyword & m_high
    if cfg.require_high_for_crossborder:
        m_xborder = m_xborder & m_high
    if cfg.exclude_structuring_from_crossborder:
        m_xborder = m_xborder & (~m_struct)

    # Avancerade masker
    m_velocity = _rule_velocity(df, cfg.velocity_window_hours, cfg.velocity_min_tx)
    m_pingpong = _rule_pingpong(df, cfg.pingpong_days, cfg.pingpong_min_pairs)
    m_newcp    = _rule_new_counterparty(df, cfg.new_counterparty_days, cfg.require_high_for_new_counterparty, m_high)

    # Slutlig OR av alla
    any_flag = m_high | m_xborder | m_struct | m_keyword | m_velocity | m_pingpong | m_newcp
    if not any_flag.any():
        return pd.DataFrame(columns=["transaction_id", "reason", "flagged_date", "amount"])

    # Reason-texter per rad
    reasons = []
    for i in df.index:
        if not any_flag.get(i, False):
            reasons.append("")
            continue
        rlist = []
        if bool(m_high.get(i, False)):
            rlist.append("High amount vs p98 (per valuta)")
        if bool(m_xborder.get(i, False)):
            rlist.append("High-value cross-border (strict)")
        if bool(m_struct.get(i, False)):
            lo, hi = cfg.structuring_by_currency.get(str(df.at[i, "currency"]), (None, None))
            if lo is not None:
                rlist.append(f"Structuring band {lo:g}–{hi:g} {df.at[i,'currency']}")
        if bool(m_keyword.get(i, False)):
            rlist.append("Keyword + high amount" if cfg.require_high_for_keyword else "Keyword match in notes")
        if bool(m_velocity.get(i, False)):
            rlist.append(f"High velocity ≥ {cfg.velocity_min_tx} tx/{cfg.velocity_window_hours}h")
        if bool(m_pingpong.get(i, False)):
            rlist.append(f"Ping-pong (retur inom {cfg.pingpong_days}d)")
        if bool(m_newcp.get(i, False)):
            extra = " + high amount" if cfg.require_high_for_new_counterparty else ""
            rlist.append(f"New counterparty (>{cfg.new_counterparty_days}d){extra}")

        reasons.append(", ".join(rlist))

    flagged = df.loc[any_flag].copy()
    flagged["reason"] = [r for r in reasons if r]
    flagged["flagged_date"] = pd.Timestamp.today().date().isoformat()
    flagged = flagged[["transaction_id", "reason", "flagged_date", "amount"]].drop_duplicates()

    if cfg.cap_per_reason:
        flagged = (
            flagged.sort_values("amount", ascending=False)
                   .groupby("reason", group_keys=False)
                   .head(cfg.cap_per_reason)
        )

    return flagged
