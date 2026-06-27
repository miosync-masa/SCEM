#!/usr/bin/env python3
"""
ess_acquire.py — ESS(European Social Survey)integrated rounds を slim parquet 化する。

ESS API(https://api.ess.sikt.no/docs)経由で取得する。**User ID は認証でなく利用統計用**だが、
公開リポジトリに焼かないため **環境変数 ESS_USER_ID から読む**(コミットしない)。
  endpoint: GET /v1/data/dataFile/{doiPrefix}/{doiSuffix}?userId=...&fileFormat=parquet
  fileFormat=parquet を直接取得(Stata 解析不要)。recodeMissingValues=1 で欠損を NaN 化。

取得:
  export ESS_USER_ID="<あなたのESS User ID>"   # https://ess.sikt.no/en/api で確認(認証ではない)
  python3 src/ess_acquire.py                    # ROUND_DOIS を API DL → slim parquet
既に data/ess/ に ESS*.parquet / *.dta / *.sav があればそれを使う(再DLしない)。

生データ(data/ess/)は .gitignore(リポジトリに入れない)。捏造なし=実データのみ。
core 変数(freehms / euftf / 移民3項 / デモグラ / weight)は全 round 共通。

Run: ESS_USER_ID=... python3 src/ess_acquire.py
"""
from __future__ import annotations
import os
import sys
import urllib.request
from pathlib import Path
import pandas as pd

# ESS integrated rounds の DOI suffix(2026-06-27 時点で API が返す最新編集版)。
API = "https://api.ess.sikt.no/v1/data/dataFile/10.21338"
ROUND_DOIS = {7: "ess7e02_2", 8: "ess8e02_3", 9: "ess9e03_1", 10: "ess10e03_1", 11: "ess11e03_0"}

ROOT = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent
ESS_DIR = ROOT / "data" / "ess"

# 必要列(ESS core)。実ファイルに在る列だけ採用(round で揺れる前提で防御的)。
NEED = [
    # 3本柱(柱=pillar)
    "freehms",                              # LGBT寛容(1 agree strongly … 5 disagree strongly)
    "euftf",                                # EU統合(0 gone too far … 10 go further)
    "imbgeco", "imueclt", "imwbcnt",        # 移民(各 0 bad/undermine/worse … 10 good/enrich/better)
    # デモグラ(proxy 軸)
    "cntry", "yrbrn", "agea", "gndr",
    "eduyrs", "edulvlb", "edulvla",         # 教育(年数 / ISCED 新旧)
    "domicil",                              # 都市度(1 big city … 5 farm/countryside)
    "rlgdgr", "rlgblg",                     # 宗教度 / 所属
    "brncntr", "facntr", "mocntr", "blgetmg",  # 移民背景(本人/父/母 国内生 / 少数民族帰属)
    # 重み・ラウンド
    "anweight", "pspwght", "pweight", "dweight", "essround", "idno",
]


def download_via_api(user_id: str):
    """ROUND_DOIS を ESS API から parquet 取得(欠損 NaN 化)。既存ファイルは再DLしない。"""
    for r, suf in ROUND_DOIS.items():
        out = ESS_DIR / f"ESS{r}.parquet"
        if out.exists() and out.stat().st_size > 100_000:
            print(f"[skip] ESS{r} 既存")
            continue
        url = f"{API}/{suf}?userId={user_id}&fileFormat=parquet&recodeMissingValues=1"
        print(f"[download] ESS{r} ({suf}) …")
        urllib.request.urlretrieve(url, out)
        if out.stat().st_size < 100_000:
            out.unlink(missing_ok=True)
            print(f"  ⚠️ ESS{r} 取得失敗(DOI 改訂の可能性: {suf})")


def read_one(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
        return df[[c for c in NEED if c in df.columns]]
    if path.suffix == ".dta":
        cols_in = set(pd.io.stata.StataReader(str(path)).variable_labels().keys())
        return pd.read_stata(str(path), columns=[c for c in NEED if c in cols_in],
                             convert_categoricals=False)
    df = pd.read_spss(str(path))   # .sav(pyreadstat 要)。Stata/parquet 推奨。
    return df[[c for c in NEED if c in df.columns]]


def main():
    ESS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(ESS_DIR.glob("*.parquet")) + sorted(ESS_DIR.glob("*.dta")) + sorted(ESS_DIR.glob("*.sav"))
    files = [p for p in files if p.name != "ess_slim.parquet"]
    if not files:
        uid = os.environ.get("ESS_USER_ID")
        if uid:
            download_via_api(uid)
            files = sorted(ESS_DIR.glob("*.parquet"))
            files = [p for p in files if p.name != "ess_slim.parquet"]
        if not files:
            print("⚠️ data/ess/ に ESS ファイルがありません。")
            print("   ESS API で取得: export ESS_USER_ID=<your-ESS-user-id>; python3 src/ess_acquire.py")
            print("   User ID は https://ess.sikt.no/en/api(認証でなく利用統計用)。詳細 docs/ess_validation_plan.md §D。")
            raise SystemExit(1)
    frames = []
    for p in files:
        try:
            d = read_one(p)
            d["_srcfile"] = p.name
            frames.append(d)
            print(f"[read] {p.name}: rows={len(d)} cols={d.shape[1]}")
        except Exception as e:
            print(f"[skip] {p.name}: {e}")
    if not frames:
        raise SystemExit("読み込めるファイルがありませんでした。")
    df = pd.concat(frames, ignore_index=True)
    out = ESS_DIR / "ess_slim.parquet"
    df.to_parquet(out)
    miss = [c for c in NEED if c not in df.columns]
    print(f"[saved] {out.relative_to(ROOT)} rows={len(df)} cols={df.shape[1]}")
    if "essround" in df.columns:
        print("  rounds:", sorted(df["essround"].dropna().unique().tolist()))
    if "cntry" in df.columns:
        print("  countries:", len(df["cntry"].dropna().unique()))
    if miss:
        print(f"  注意: 当該ファイルに無い列(後段で防御的に扱う): {miss}")


if __name__ == "__main__":
    main()
