"""
media_generation_v5.py — 実データ156件接続版

設計:
  - v4の計算エンジン(カーブ/3モード/干渉/REFRAME発火/独立性判定)を丸ごと再利用
  - データだけ event_loader 経由の156件に差し替え
  - 個別 sensitivity_peak_age があればそれでカーブを作り、無ければv4のCURVESにフォールバック(ハイブリッド)
  - エンジン本体(v4)は1行も書き換えない → 既存の検証結果が壊れない

使い方:
    python media_generation_v5.py 1981
"""
from __future__ import annotations
import sys
import media_generation_v4 as v4
import event_loader as L


# ── ローダーEvent → v4 Event 変換 ──
def to_v4_event(le: L.Event) -> v4.Event:
    # Domain/Mode の enum をv4側へ載せ替え(名前一致で対応)
    try:
        v4_domain = v4.Domain[le.domain.name]
    except KeyError:
        # v4に無いDomain(PLATFORM/LIFESTYLE/PRICE等)はMEDIA扱いにせず、
        # 最も近い既存カーブへマップ。無ければ後段のフォールバックに任せUNKNOWN相当に。
        v4_domain = _map_domain(le.domain)
    v4_mode = v4.Mode[le.mode.name]

    ev = v4.Event(
        name=le.name,
        year=le.year,
        domain=v4_domain,
        mode=v4_mode,
        agency=le.agency,
        description=le.description,
        reframe_group=le.reframe_group,
        reference_value=le.reference_value,
        region_dependent=le.region_dependent,
        reversible=le.reversible,
        salience=le.salience,
        effect_vector=dict(le.effect_vector),
    )
    # 個別感受性をブリッジ属性として保持(下のpatched_sensitivityが読む)
    ev._peak_age = le.peak_age      # type: ignore[attr-defined]
    ev._spread = le.spread          # type: ignore[attr-defined]
    return ev


# v4が11領域フル対応したので、Domainマッピングは原則不要。
# 名前一致でそのまま載せ替える。万一v4に無いDomain(FOOD等で名前不一致)なら
# 近縁へマップ、それでも無ければPOLITICS(中庸カーブ)を既定にする。
_DOMAIN_MAP = {
    # ローダーにあってv4に無い可能性のあるものだけ近縁マップ(保険)
    "FOOD": "FOOD",
}


def _map_domain(loader_domain) -> "v4.Domain":
    name = loader_domain.name
    try:
        return v4.Domain[name]
    except KeyError:
        mapped = _DOMAIN_MAP.get(name)
        if mapped:
            try:
                return v4.Domain[mapped]
            except KeyError:
                pass
        return v4.Domain.POLITICS


# ── 個別感受性を優先する sensitivity に差し替え ──
_original_mode_weight = v4.mode_weight


def patched_mode_weight(ev: "v4.Event", age: int) -> float:
    """個別 peak_age があれば個別カーブで s を計算、無ければv4 CURVES。
    mode別の重み付け(PASSIVE/ACTIVE/REFRAME)はv4のロジックをそのまま踏襲。"""
    peak = getattr(ev, "_peak_age", None)
    if peak is not None:
        spread = getattr(ev, "_spread", None) or 6.0
        curve = v4.SensitivityCurve(peak=peak, left_width=spread, right_width=spread * 1.5,
                                    floor=0.10)
        s = curve(age)
    else:
        s = v4.sensitivity(age, ev.domain, ev.mode)

    if ev.mode is v4.Mode.PASSIVE:
        return s * ev.salience
    if ev.mode is v4.Mode.ACTIVE:
        return s * (0.30 + 0.70 * ev.agency) * ev.salience
    if ev.mode is v4.Mode.REFRAME:
        return s * (0.50 + 0.50 * ev.agency) * ev.salience
    raise ValueError(f"unknown mode: {ev.mode}")


# エンジンのmode_weightを差し替え(analyzeはこれを呼ぶ)
v4.mode_weight = patched_mode_weight


def load_events(path: str = "events_patched.jsonl") -> list["v4.Event"]:
    loader_events, errors = L.load_jsonl(path)
    if errors:
        print(f"[warn] {len(errors)}件スキップ", file=sys.stderr)
    return [to_v4_event(e) for e in loader_events]


# ───────────────────────────────────────────────
# 3軸レポート: PASSIVE/ACTIVE/REFRAMEを同列に並べず、別の量として扱う
# ───────────────────────────────────────────────
def mode_density(hits: list[dict], mode: "v4.Mode") -> dict:
    """あるモードの『密度』= そのモードの作用がどれだけ濃く着弾したか。
    各モードは単位が違うので、生の合計ではなく
    『着弾件数で正規化した平均weight』と『上位の厚み』を両方見る。"""
    ms = [h for h in hits if h["ev"].mode is mode]
    if not ms:
        return {"count": 0, "mean": 0.0, "top3_mean": 0.0, "sum": 0.0}
    ws = sorted((h["weight"] for h in ms), reverse=True)
    top3 = ws[:3]
    return {
        "count": len(ms),
        "mean": round(sum(ws) / len(ws), 3),
        "top3_mean": round(sum(top3) / len(top3), 3),
        "sum": round(sum(ws), 3),
    }


def report_3axis(birth_year: int, events: list["v4.Event"], top_n: int = 8):
    hits, interferences, reframe_fires, overlap = v4.analyze(birth_year, events)

    print("=" * 68)
    print(f"  {birth_year}年生まれ — 3軸作用プロファイル")
    print("=" * 68)

    # ── 世代の3次元座標(指紋) ──
    dP = mode_density(hits, v4.Mode.PASSIVE)
    dA = mode_density(hits, v4.Mode.ACTIVE)
    dR = mode_density(hits, v4.Mode.REFRAME)
    print("\n【世代指紋 — 作用モードの構成比(同列にしない3つの量)】")
    print(f"  PASSIVE(刷り込みの濃さ)  : 件数{dP['count']:>3}  平均{dP['mean']:.2f}  top3{dP['top3_mean']:.2f}")
    print(f"  ACTIVE (人生分岐の重さ)  : 件数{dA['count']:>3}  平均{dA['mean']:.2f}  top3{dA['top3_mean']:.2f}")
    print(f"  REFRAME(基準ずらしの幅)  : 件数{dR['count']:>3}  平均{dR['mean']:.2f}  top3{dR['top3_mean']:.2f}")

    # ── 軸1: PASSIVE 何が濃く刷り込まれたか ──
    print("\n【軸1 PASSIVE — 何が身体に刷り込まれたか(浸透の深さ順)】")
    ps = sorted((h for h in hits if h["ev"].mode is v4.Mode.PASSIVE), key=lambda h: -h["weight"])
    for h in ps[:top_n]:
        ev = h["ev"]
        print(f"  [{h['weight']:.2f}] {ev.name:<22} {h['age']:>2}歳 {h['stage']:<7} {ev.domain.value}")

    # ── 軸2: ACTIVE 何が人生を分岐させたか ──
    print("\n【軸2 ACTIVE — 何が意思決定を迫ったか(分岐の重さ順)】")
    as_ = sorted((h for h in hits if h["ev"].mode is v4.Mode.ACTIVE), key=lambda h: -h["weight"])
    if not as_:
        print("  (なし)")
    for h in as_[:top_n]:
        ev = h["ev"]
        print(f"  [{h['weight']:.2f}] {ev.name:<22} {h['age']:>2}歳 {h['stage']:<7} agency={ev.agency:.2f} {ev.domain.value}")

    # ── 軸3: REFRAME 何が基準値をずらしたか(発火順) ──
    print("\n【軸3 REFRAME — 何が『普通』の基準をずらしたか(差分発火順)】")
    if not reframe_fires:
        print("  (発火なし)")
    seen = set()
    for r in reframe_fires[:top_n]:
        key = r["group"]
        if key in seen:
            continue
        seen.add(key)
        a_name, a_age, _ = r["anchor"]
        t_name, t_age, _ = r["trigger"]
        print(f"  [{r['fire']:.2f}] {r['group']}: {a_name}({a_age}歳) → {t_name}({t_age}歳) Δ={r['delta']:.2f}")

    # ── 干渉ノード(モードをまたぐ同時着弾) ──
    print("\n【干渉ノード — 同じ認知段階バンドへの同時着弾(世代の質感)】")
    for it in interferences[:top_n]:
        x = "横断⚡" if it["cross_domain"] else "同領域"
        lo, hi = it["age_range"]
        print(f"  [{it['score']:.2f}] {it['stage']:<6} {it['pair'][0]} × {it['pair'][1]} ({lo}-{hi}歳 {x})")
    print()


if __name__ == "__main__":
    birth = int(sys.argv[1]) if len(sys.argv) > 1 else 1981
    path = sys.argv[2] if len(sys.argv) > 2 else "events_patched.jsonl"
    events = load_events(path)
    print(f"[info] {len(events)}件を {birth}年生まれで分析\n")
    report_3axis(birth, events)


# ───────────────────────────────────────────────
# 多世代バッチ: 世代指紋(3軸構成比)の変遷を一覧化
# ───────────────────────────────────────────────
def cohort_fingerprint(birth_year: int, events: list["v4.Event"]) -> dict:
    hits, interferences, reframe_fires, _ = v4.analyze(birth_year, events)
    dP = mode_density(hits, v4.Mode.PASSIVE)
    dA = mode_density(hits, v4.Mode.ACTIVE)
    dR = mode_density(hits, v4.Mode.REFRAME)
    # 人格形成期(12-17)に着弾した上位事象=その世代の"原体験"
    teen = sorted((h for h in hits if h["stage"] == "人格形成期"),
                  key=lambda h: -h["weight"])[:3]
    # 干渉ノードの筆頭(質感)
    top_interf = interferences[0] if interferences else None
    # REFRAME発火の筆頭
    top_fire = reframe_fires[0] if reframe_fires else None
    return {
        "birth": birth_year,
        "P": dP, "A": dA, "R": dR,
        "teen_top": [(h["ev"].name, h["age"], h["weight"]) for h in teen],
        "interf": (top_interf["pair"], top_interf["stage"]) if top_interf else None,
        "fire": (top_fire["group"], top_fire["fire"]) if top_fire else None,
    }


def batch_compare(birth_years: list[int], events: list["v4.Event"]):
    prints = [cohort_fingerprint(by, events) for by in birth_years]

    print("=" * 78)
    print("  多世代バッチ — 世代指紋(3軸構成比)の変遷")
    print("=" * 78)
    print("\n【作用モード密度: 平均weight (件数)】")
    print(f"  {'生年':<6}{'PASSIVE':>14}{'ACTIVE':>14}{'REFRAME':>14}   支配モード")
    for p in prints:
        P, A, R = p["P"]["mean"], p["A"]["mean"], p["R"]["mean"]
        dom = max([("PASSIVE", P), ("ACTIVE", A), ("REFRAME", R)], key=lambda x: x[1])[0]
        print(f"  {p['birth']:<6}{P:>8.2f}({p['P']['count']:>3}){A:>8.2f}({p['A']['count']:>3})"
              f"{R:>8.2f}({p['R']['count']:>3})   {dom}")

    print("\n【各世代の人格形成期(12-17歳)原体験 Top3】")
    for p in prints:
        items = " / ".join(f"{n}({a}歳)" for n, a, w in p["teen_top"])
        print(f"  {p['birth']}: {items}")

    print("\n【各世代の質感(干渉ノード筆頭)】")
    for p in prints:
        if p["interf"]:
            pair, stage = p["interf"]
            print(f"  {p['birth']}: [{stage}] {pair[0]} × {pair[1]}")
        else:
            print(f"  {p['birth']}: (干渉なし)")

    print("\n【各世代のREFRAME発火筆頭】")
    for p in prints:
        if p["fire"]:
            grp, fire = p["fire"]
            print(f"  {p['birth']}: {grp} (fire={fire:.2f})")
        else:
            print(f"  {p['birth']}: (発火なし)")
    print()
