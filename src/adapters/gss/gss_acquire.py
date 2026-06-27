#!/usr/bin/env python3
"""
gss_acquire.py — GSS 1972–2024 Cumulative(Stata)を取得し、必要列だけ slim parquet 化する。

生データ(570MB の gss7224_r3.dta)は data/gss/ に置き、.gitignore 済(リポジトリに入れない)。
本スクリプトで誰でも再取得できる(NORC 無料公開・NSF 資金)。捏造なし・実データのみ。

Run: python3 src/gss_acquire.py
出力: data/gss/GSS_stata.zip(45MB) / data/gss/gss7224_r3.dta(570MB) / data/gss/gss_slim.parquet(~2MB)
"""
from __future__ import annotations
import sys, zipfile, urllib.request
from pathlib import Path
import pandas as pd

ROOT = next(_p for _p in Path(__file__).resolve().parents if _p.name == "src").parent
GSS_DIR = ROOT / "data" / "gss"
URL = "https://gss.norc.org/content/dam/gss/get-the-data/documents/stata/GSS_stata.zip"
DTA = GSS_DIR / "gss7224_r3.dta"

# Paper 2 GSS spec で使う列(§8)。デモグラ + 態度 + 信頼 + 重み。
NEED = ["year", "cohort", "age", "reltrad", "reltrad16", "relig", "denom", "other",
        "race", "hispanic", "region", "region_7222", "srcbelt", "xnorcsiz", "degree", "educ",
        "attend", "fund", "marsame", "marsame1", "marsamey",
        "abany", "abdefect", "abrape", "gunlaw",
        "letin1a", "letinhsp", "letinasn", "immjobs", "immcrime", "racopen",
        "confinan", "confed", "conlegis", "conarmy", "wtssall", "wtssps", "wtssnrps", "ballot", "id"]


def main():
    GSS_DIR.mkdir(parents=True, exist_ok=True)
    if not DTA.exists():
        zp = GSS_DIR / "GSS_stata.zip"
        if not zp.exists():
            print(f"[download] {URL}")
            urllib.request.urlretrieve(URL, zp)
        print(f"[unzip] {zp.name}")
        with zipfile.ZipFile(zp) as z:
            z.extractall(GSS_DIR)
    print(f"[read] {DTA.name}(必要列のみ {len(NEED)} 列)")
    cols = set(pd.io.stata.StataReader(str(DTA)).variable_labels().keys())
    use = [c for c in NEED if c in cols]
    missing = [c for c in NEED if c not in cols]
    if missing:
        print(f"  注意: 当該 release に無い列(スキップ): {missing}")
    df = pd.read_stata(str(DTA), columns=use, convert_categoricals=False)
    out = GSS_DIR / "gss_slim.parquet"
    df.to_parquet(out)
    print(f"[saved] {out.relative_to(ROOT)}  rows={len(df)} cols={len(use)}")


if __name__ == "__main__":
    main()
