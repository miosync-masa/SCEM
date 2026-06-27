#!/usr/bin/env python3
"""
ess_segments.py — ESS(UK/Europe)版セグメント設計。GSS の gss_segments を移植。

肝(依頼 §3/§5):
  - EVENT_STRUCTURE を ESS の 3本柱にも事前にかける(銃の教訓)。反復イベントの flat を「CMR外れ」と
    誤読しない。freehms=単発(主検証)/ euftf=反復疑い / 移民=反復濃厚。
  - 共同体軸は US と違う(階級/EU距離/religiosity/country)。proxy 的に定義(フルクロスしない)。
    軸が違っても high-flat/transition の二分が再現するか=CMR の普遍性(§5)。

ESS コーディング(documented; 実データで ess_acquire 後に値域を検証する前提で防御的):
  freehms 1 agree strongly … 5 disagree strongly(>5=欠損)。寛容 = {1,2}。
  euftf 0 gone too far … 10 go further(>10=欠損)。Pro-EU = 高。
  imbgeco/imueclt/imwbcnt 0 bad/undermine/worse … 10 good/enrich/better(>10=欠損)。Pro = 高。
  yrbrn 出生年(>=7777 欠損)/ eduyrs 教育年数 / edulvlb ISCED詳細 / domicil 1 big city…5 farm /
  rlgdgr 0 not at all…10 very / brncntr,facntr,mocntr 1 yes 2 no(本人/父/母 国内生)。
重み:anweight 優先(無ければ pspwght×pweight、無ければ pspwght、無ければ 1)。
"""
from __future__ import annotations
import numpy as np
import pandas as pd

# 事象の時間構造(銃の教訓の移植)。反復は出生年軸で原理的に観測しにくい=flat を誤読しない。
EVENT_STRUCTURE = {
    "freehms": "single_moment",              # LGBT合法化モーメント(GSS同性婚と対応)=主検証
    "euftf": "recurrent_burst_suspected",    # EU統合(反復:マーストリヒト→危機→Brexit)
    "immigration": "recurrent_burst",        # 移民(慢性・選挙毎バースト・全世代継続曝露)
}


def _miss(s, hi):
    """値域 [0,hi] 外を NaN に(ESS の 77/88/99 等の欠損コードを落とす)。"""
    return s.where((s >= 0) & (s <= hi))


# ── 3本柱の outcome(進歩派/寛容方向に揃える)──
def freehms_tolerant(d):
    """LGBT寛容 = freehms ∈ {1,2}(agree)→1, {3,4,5}→0。二値(GSS同性婚と同型)。"""
    v = _miss(d["freehms"], 5)
    out = pd.Series(pd.NA, index=d.index, dtype="Float64")
    out[v.isin([1, 2])] = 1.0
    out[v.isin([3, 4, 5])] = 0.0
    return out


def euftf_pro(d):
    """EU統合賛成 = euftf(0–10, 高=go further)。連続。"""
    return _miss(d["euftf"], 10).astype("Float64")


def immigration_index(d):
    """移民賛成 index = mean(imbgeco, imueclt, imwbcnt)(各 0–10, 高=pro)。連続。"""
    cols = [_miss(d[c], 10) for c in ["imbgeco", "imueclt", "imwbcnt"] if c in d]
    if not cols:
        return pd.Series(np.nan, index=d.index)
    return pd.concat(cols, axis=1).mean(axis=1)


PILLARS = {
    "freehms": (freehms_tolerant, "binary", "single_moment"),
    "euftf": (euftf_pro, "continuous", "recurrent_burst_suspected"),
    "immigration": (immigration_index, "continuous", "recurrent_burst"),
}


# ── proxy 軸ヘルパ ──
def high_edu(d):
    """高学歴 proxy:edulvlb(ISCED)で tertiary(>=600)優先、無ければ eduyrs>=15。"""
    if "edulvlb" in d and d["edulvlb"].notna().any():
        e = d["edulvlb"].where(d["edulvlb"] < 5500)   # 欠損(5555等)除外
        return e >= 600
    return _miss(d["eduyrs"], 40) >= 15


def low_edu(d):
    if "edulvlb" in d and d["edulvlb"].notna().any():
        e = d["edulvlb"].where(d["edulvlb"] < 5500)
        return e < 600
    return _miss(d["eduyrs"], 40) < 13


def secular(d):   return _miss(d["rlgdgr"], 10) <= 3
def religious(d): return _miss(d["rlgdgr"], 10) >= 7
def urban(d):     return d["domicil"].isin([1, 2])
def rural(d):     return d["domicil"].isin([4, 5])


def immigrant_bg(d):
    """移民背景:本人 or 父 or 母が国外生(brncntr/facntr/mocntr == 2)。"""
    cond = pd.Series(False, index=d.index)
    for c in ["brncntr", "facntr", "mocntr"]:
        if c in d:
            cond = cond | (d[c] == 2)
    return cond


def native_bg(d):
    cond = pd.Series(True, index=d.index)
    for c in ["brncntr", "facntr", "mocntr"]:
        if c in d:
            cond = cond & (d[c] == 1)
    return cond


# ── proxy セグメント(GSS Coastal vs Bible Belt の ESS 類似。普遍性検証用)──
# REFRAME 側(寛容が既に基準化=flat-high の予測)/ ACTIVE・移行側(出生年勾配の予測)。
SEGMENTS = {
    # 主対比(freehms step1):secular高学歴都市(=Coastal類似) vs 宗教的低学歴(=Bible Belt類似)
    "Secular HiEdu Urban": lambda d: secular(d) & high_edu(d) & urban(d),
    "Religious LowEdu":    lambda d: religious(d) & low_edu(d),
    # 一軸ロバストネス
    "Secular (all)":   lambda d: secular(d),
    "Religious (all)": lambda d: religious(d),
    "HiEdu (all)":     lambda d: high_edu(d),
    "LowEdu (all)":    lambda d: low_edu(d),
    # 移民背景(euftf/移民 柱で効く想定)
    "Immigrant-bg":    lambda d: immigrant_bg(d),
    "Native HiEdu Urban": lambda d: native_bg(d) & high_edu(d) & urban(d),
}
PRIMARY_CONTRAST = ["Secular HiEdu Urban", "Religious LowEdu"]   # step1 主対比


def segment_mask(d, name):
    return SEGMENTS[name](d)


def weight(d):
    """ESS 解析重み:anweight 優先 → pspwght×pweight → pspwght → 1。"""
    if "anweight" in d and d["anweight"].notna().any():
        return d["anweight"].fillna(0.0)
    if "pspwght" in d and "pweight" in d:
        return (d["pspwght"] * d["pweight"]).fillna(0.0)
    if "pspwght" in d:
        return d["pspwght"].fillna(0.0)
    return pd.Series(1.0, index=d.index)


def cohort_bin(d, width=10):
    c = _miss(d["yrbrn"], 2025)
    return (c // width * width).where(c.notna())
