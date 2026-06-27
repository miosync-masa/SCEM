#!/usr/bin/env python3
"""
gss_segments.py — GSS cumulative から CMR 8 共同体(premise セグメント)を構築する。

Paper 2(CMR)の予算ゼロ実証(GSS 二次分析 spec, 環)用。SCEM の premise セグメントを
GSS 変数の論理式で操作化する。**分類は自作せず、GSS 公式変数を使う**:
  - 宗教 = 公式 `reltrad`(RELTRAD; Steensland et al. 2000。NORC/ARDA 計算済みが cumulative に同梱)
           → Burge syntax を移植する必要なし。Mormon だけ reltrad では "other faith" に吸収されるため
             `other`(具体宗派)コードで別抽出(spec §4.2)。

このファイルで判明した GSS 2024 release の実装上の注意(docs/gss_data_realities.md に詳述):
  - **9 区分の地理は `region` ではなく `region_7222`**。2024 release で `region` は 4 区分 census
    region(northeast/midwest/south/west)に変更された。9 区分(new england…pacific)は
    `region_7222` に退避し、**2022 までで打ち切り**(2024 は欠損)。
  - **同性婚は 3 変数に分割**:`marsame`(1988/2004/2021/2022/2024)+ `marsame1`(2006–2018)
    + `marsamey`(2024)。接続して 12 波の時系列にする(spec §3.3 の「接続必須」の正体)。
    3 変数とも 1–5(1=strongly agree … 5=strongly disagree)同一スケール。
  - **hispanic は 2000 年以降のみ**。白人セグメントで `hispanic==1`(非ヒス)を必須にすると
    1988 など重要な早期波が全消しになる。よって白人 = race==white かつ
    (hispanic 欠損 or 非ヒス)= 2000 以前は race=white で近似(構築上の選択。明示する)。

欠損: convert_categoricals=False で読むと Stata の拡張欠損は NaN。GSS の IAP/DK/NA は NaN。
"""
from __future__ import annotations
import pandas as pd

# ── 補助マスク(再利用) ──
def white_nonhisp(d: pd.DataFrame) -> pd.Series:
    """非ヒスパニック白人。hispanic は 2000+ のみ存在 → 欠損年は race=white で近似(早期波保持)。"""
    return (d.race == 1) & (d.hispanic.isna() | (d.hispanic == 1))


def hispanic_any(d: pd.DataFrame) -> pd.Series:
    """ヒスパニック(2000+ のみ判定可能。それ以前は False=判定不能)。"""
    return d.hispanic.notna() & (d.hispanic > 1)


def is_mormon(d: pd.DataFrame) -> pd.Series:
    """Mormon は reltrad では other faith(6)に吸収 → `other` 具体宗派コードで抽出(60/64/162)。"""
    return d.other.isin([60, 64, 162])


# ── 8 共同体セグメント(spec §4.1。reltrad / region_7222(9区分) / srcbelt(都市度) を使い分け) ──
# region_7222: 1 NewEng 2 MidAtl 3 ENC 4 WNC 5 S.Atl 6 ESC 7 WSC 8 Mountain 9 Pacific
# srcbelt:     1,2 central city / 3,4 suburbs / 5 other urban / 6 other rural
# degree:      0 LT-HS 1 HS 2 assoc/jc 3 bachelor 4 graduate
# reltrad:     1 evangelical 2 mainline 3 black-prot 4 catholic 5 jewish 6 other 7 nonaffiliated
SEGMENTS = {
    # 主力6(N 厚い → 強く主張)
    "Coastal Liberal": lambda d: (d.reltrad == 7) & white_nonhisp(d)
        & d.region_7222.isin([1, 9]) & (d.degree == 4),
    "Bible Belt": lambda d: (d.reltrad == 1) & white_nonhisp(d)
        & d.region_7222.isin([5, 6, 7]) & (d.degree <= 1),
    "Rust Belt WWC": lambda d: (d.reltrad == 2) & white_nonhisp(d)
        & d.region_7222.isin([2, 3]) & (d.degree <= 1),
    "Black urban": lambda d: d.reltrad.isin([3, 7]) & (d.race == 2)
        & d.srcbelt.isin([1, 2]) & (d.degree == 2),
    "Suburban MC": lambda d: (d.reltrad == 2) & white_nonhisp(d)
        & d.srcbelt.isin([3, 4]) & (d.degree == 3),
    "Rural Conservative": lambda d: (d.reltrad == 1) & white_nonhisp(d)
        & (d.srcbelt == 6) & (d.degree <= 1),
    # 補助2(N 薄い → 弱く主張。Latino は 2000+、Mormon は other 抽出)
    "Latino Immigrant": lambda d: (d.reltrad == 4) & hispanic_any(d)
        & d.srcbelt.isin([1, 2]) & (d.degree == 2),
    "Mormon": lambda d: is_mormon(d) & white_nonhisp(d)
        & (d.region_7222 == 8) & (d.degree == 3),
}

PRIMARY = ["Coastal Liberal", "Bible Belt", "Rust Belt WWC",
           "Black urban", "Suburban MC", "Rural Conservative"]
SUPPLEMENTARY = ["Latino Immigrant", "Mormon"]


def segment_mask(df: pd.DataFrame, name: str) -> pd.Series:
    return SEGMENTS[name](df)


# ── 態度変数の接続 ──
def ssm_approve(df: pd.DataFrame) -> pd.Series:
    """同性婚 賛成(approve)= 1 / 反対=0 / 未回答=NaN。
    marsame(1988/2004/2021/2022/2024) + marsame1(2006–2018) + marsamey(2024) を接続。
    3 変数とも 1=strongly agree … 5=strongly disagree。approve = code in {1,2}。"""
    raw = df["marsame"].copy()
    if "marsame1" in df:
        raw = raw.fillna(df["marsame1"])
    if "marsamey" in df:
        raw = raw.fillna(df["marsamey"])
    out = pd.Series(pd.NA, index=df.index, dtype="Float64")
    out[raw.isin([1, 2])] = 1.0
    out[raw.isin([3, 4, 5])] = 0.0
    return out


def cohort_bin(df: pd.DataFrame, width: int = 5) -> pd.Series:
    """出生年(cohort)を width 年刻みのビン下端へ(暫定5年, spec §6.1)。"""
    c = df["cohort"]
    return (c // width * width).where(c.notna())
