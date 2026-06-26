#!/usr/bin/env python3
"""
ess_acquire.py — ESS(European Social Survey)integrated rounds を slim parquet 化する。

⚠️ ESS は登録制で配布が SAS トークン認証付き → 自動ダウンロード不可(GSS と違う)。
手動取得が必要(無料):
  1. ESS Data Portal で登録・ログイン:
       https://www.europeansocialsurvey.org/  /  https://ess-search.nsd.no/
  2. integrated rounds(ESS1–ESS11)の **Stata 形式** をダウンロード
       (per-round の ESS1..ESS11 でも、cumulative/Data Wizard 抽出でも可)
  3. ダウンロードした .dta(または .sav)を data/ess/ に置く(複数可)
  4. python3 src/ess_acquire.py   → data/ess/ess_slim.parquet を生成

生データ(data/ess/)は .gitignore(リポジトリに入れない)。捏造なし=実データのみ。
core モジュール変数(freehms / euftf / 移民3項 / デモグラ / weight)は全 round 共通で取れる。

Run: python3 src/ess_acquire.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
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


def read_one(path: Path) -> pd.DataFrame:
    cols_in = set((pd.io.stata.StataReader(str(path)).variable_labels().keys()
                   if path.suffix == ".dta" else []))
    if path.suffix == ".dta":
        use = [c for c in NEED if c in cols_in]
        df = pd.read_stata(str(path), columns=use, convert_categoricals=False)
    else:  # .sav 等は pyreadstat が要るので Stata 推奨。ここは簡易対応。
        df = pd.read_spss(str(path))
        df = df[[c for c in NEED if c in df.columns]]
    return df


def main():
    ESS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted([p for p in ESS_DIR.glob("*.dta")] + [p for p in ESS_DIR.glob("*.sav")])
    if not files:
        print("⚠️ data/ess/ に ESS ファイル(.dta/.sav)がありません。")
        print("   ESS Data Portal で登録・ログイン → integrated rounds(Stata)を DL → data/ess/ に配置。")
        print("   詳細は本スクリプト冒頭 docstring / docs/ess_validation_plan.md §D。")
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
