"""
compare_picks.py — 世代別pickリストを軸ごとに時系列で並べて見る

使い方:
    python compare_picks.py             # 全軸を並べる
    python compare_picks.py music       # 音楽軸だけ
    python compare_picks.py sport       # スポーツ軸だけ
"""
import os
import sys
import json
import glob


PICKS_DIR = "picks_cache"
AXIS_LABELS = {
    "music": "🎵 音楽軸",
    "sport": "⚽ スポーツ軸",
    "literature": "📚 文学・読書軸",
    "film": "🎬 映画・映像軸",
}


def load_all_picks() -> list[dict]:
    files = sorted(glob.glob(os.path.join(PICKS_DIR, "picks_*.json")))
    out = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if "axes" in data:
                out.append(data)
        except Exception as e:
            print(f"[skip] {path}: {e}", file=sys.stderr)
    return sorted(out, key=lambda d: d.get("birth_year", 0))


def print_axis_comparison(all_picks: list[dict], axis_key: str):
    label = AXIS_LABELS.get(axis_key, axis_key)
    print(f"\n{'='*70}")
    print(f"  {label}: 9世代の文化選択肢空間の変遷")
    print(f"{'='*70}")
    for data in all_picks:
        by = data.get("birth_year")
        axis = data.get("axes", {}).get(axis_key, {})
        picks = axis.get("picks", [])
        print(f"\n  ── {by}年生まれ ──")
        for p in picks:
            if "その他" in p or "自由記述" in p:
                continue
            print(f"    • {p}")


if __name__ == "__main__":
    all_picks = load_all_picks()
    if not all_picks:
        print("[error] picks_cache/picks_*.json が見つかりません")
        sys.exit(1)

    print(f"[info] {len(all_picks)}世代のpickリストを読み込み: "
          f"{', '.join(str(d['birth_year']) for d in all_picks)}")

    if len(sys.argv) > 1:
        axis_key = sys.argv[1]
        if axis_key not in AXIS_LABELS:
            print(f"[error] 軸名は {list(AXIS_LABELS.keys())} のいずれか")
            sys.exit(1)
        print_axis_comparison(all_picks, axis_key)
    else:
        for k in AXIS_LABELS:
            print_axis_comparison(all_picks, k)
    print()
