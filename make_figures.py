"""
make_figures.py — Paper 1 の Figure 2 / Figure 3 を生成する。

Figure 2: 9世代バッチの3軸密度(PASSIVE/ACTIVE/REFRAME)を出生年に対してプロット。
          PASSIVE の1980-85ピークと、ACTIVE/REFRAME の単調上昇を可視化。
Figure 3: 音楽軸の文化選択肢空間を、系統ラベルの出現/消滅で示す presence ヒートマップ。
          1985/1990 と 1995/2000 の断絶線を引く。

出力: fig2_cohort_fingerprint.png, fig3_music_disruption.png

Run:
    python3 make_figures.py
"""
from __future__ import annotations
import os
import json
import glob

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

import media_generation_v5 as v5

# ── 日本語フォント ──
plt.rcParams["font.family"] = "Hiragino Sans"
plt.rcParams["axes.unicode_minus"] = False

YEARS = [1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010]
PICKS_DIR = "picks_cache"


# ───────────────────────────────────────────────
# Figure 2: 世代指紋(3軸密度)の変遷
# ───────────────────────────────────────────────
def figure2():
    events = v5.load_events()
    P, A, R = [], [], []
    for y in YEARS:
        fp = v5.cohort_fingerprint(y, events)
        P.append(fp["P"]["mean"])
        A.append(fp["A"]["mean"])
        R.append(fp["R"]["mean"])

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(YEARS, P, "o-", lw=2.4, ms=7, color="#d1495b", label="PASSIVE(刷り込みの濃さ)")
    ax.plot(YEARS, A, "s-", lw=2.2, ms=6, color="#30638e", label="ACTIVE(人生分岐の重さ)")
    ax.plot(YEARS, R, "^-", lw=2.2, ms=6, color="#3c896d", label="REFRAME(基準ずらしの幅)")

    # PASSIVE ピーク帯(1980-85)を強調
    ax.axvspan(1980, 1985, color="#d1495b", alpha=0.08, zorder=0)
    peak_idx = P.index(max(P))
    ax.annotate("PASSIVE 密度ピーク\n(1980–85年生まれ, 0.80)",
                xy=(1982.5, max(P)), xytext=(1988, 0.86),
                fontsize=10, color="#d1495b",
                arrowprops=dict(arrowstyle="->", color="#d1495b", lw=1.3))

    ax.set_xlabel("出生年", fontsize=12)
    ax.set_ylabel("作用モード密度(平均作用重み)", fontsize=12)
    ax.set_title("Figure 2. 世代指紋(3軸作用密度)の変遷 — 1970–2010年生まれ", fontsize=13, pad=12)
    ax.set_xticks(YEARS)
    ax.set_ylim(0.35, 0.92)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="lower right", fontsize=10, framealpha=0.9)
    fig.tight_layout()
    fig.savefig("fig2_cohort_fingerprint.png", dpi=200)
    plt.close(fig)
    print("[saved] fig2_cohort_fingerprint.png")


# ───────────────────────────────────────────────
# Figure 3: 音楽軸 選択肢空間の出現/消滅 ヒートマップ
# ───────────────────────────────────────────────
# 系統ラベル(行) → 検出キーワード。picksテキストに含まれれば「存在」とみなす。
# 上から古い系統 → 新しい系統の順に並べ、断絶を視覚化する。
LINEAGES = [
    ("歌謡曲・80sアイドル",       ["歌謡曲", "80年代アイドル", "松田聖子", "中森明菜"]),
    ("バンドブーム/イカ天",       ["バンドブーム", "イカ天", "BOØWY", "BLUE HEARTS"]),
    ("ビーイング/カラオケJ-POP",  ["ビーイング", "カラオケ", "ZARD", "WANDS"]),
    ("小室ファミリー/ダンス",     ["小室", "TRF", "globe", "ダンスポップ", "ダンス系J-POP"]),
    ("渋谷系/シティポップ",       ["渋谷系", "シティポップ", "Pizzicato", "Cornelius", "小沢健二"]),
    ("ヴィジュアル系",            ["ヴィジュアル系", "ビジュアル系", "X JAPAN", "LUNA SEA"]),
    ("メロコア/青春パンク",       ["メロコア", "青春パンク", "Hi-STANDARD", "MONGOL800", "175R"]),
    ("邦ロック/フェス",           ["邦ロック", "ロックフェス", "BUMP OF CHICKEN", "ASIAN KUNG-FU", "ONE OK ROCK"]),
    # HIPHOPは総称語だと全世代赤=無情報になるため、アーティストで時代別に3分割
    ("日本語ラップ黎明",           ["スチャダラパー", "EAST END", "RHYMESTER"]),
    ("ミクスチャー/J-RAP全盛",     ["Dragon Ash", "RIP SLYME", "KICK THE CAN", "m-flo", "KREVA", "湘南乃風"]),
    ("ネット/令和ラップ",          ["Creepy Nuts", "BAD HOP", "Awich", "KANDYTOWN", "JP THE WAVY", "ZORN"]),
    ("ニコ動/ボカロ/歌い手",      ["ボカロ", "ニコ", "歌い手", "初音ミク", "supercell"]),
    ("アニソン/声優",             ["アニソン", "声優", "LiSA", "水樹奈々", "アニメ主題歌", "アニメ・ゲーム"]),
    ("ジャニーズ/坂道・48",       ["ジャニーズ", "嵐", "AKB", "乃木坂", "坂道", "Snow Man", "King & Prince", "総選挙", "握手会"]),
    ("K-POP",                     ["K-POP", "K-pop", "BTS", "BLACKPINK", "TWICE", "少女時代", "NewJeans"]),
    ("サブスク令和J-POP",         ["サブスク", "令和J-POP", "YOASOBI", "髭男", "King Gnu", "Ado", "ストリーミング"]),
    ("TikTok/ショート動画発",     ["TikTok", "ショート動画", "バズ曲", "香水", "ドライフラワー"]),
]


def load_music_picks() -> dict[int, str]:
    """各世代の music picks を1本のテキストに連結して返す。"""
    out = {}
    for path in glob.glob(os.path.join(PICKS_DIR, "picks_*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        by = data.get("birth_year")
        picks = data.get("axes", {}).get("music", {}).get("picks", [])
        out[int(by)] = " | ".join(picks)
    return out


def figure3():
    music = load_music_picks()
    years = [y for y in YEARS if y in music]

    # presence 行列を作る
    import numpy as np
    M = np.zeros((len(LINEAGES), len(years)))
    for j, y in enumerate(years):
        text = music[y]
        for i, (_, kws) in enumerate(LINEAGES):
            M[i, j] = 1.0 if any(kw in text for kw in kws) else 0.0

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.imshow(M, aspect="auto", cmap="YlOrRd", vmin=0, vmax=1.4)

    # マス目に存在マーカー
    for i in range(len(LINEAGES)):
        for j in range(len(years)):
            if M[i, j] > 0:
                ax.scatter(j, i, marker="s", s=90, color="#b5172e", zorder=3)

    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([f"{y}" for y in years], fontsize=10)
    ax.set_yticks(range(len(LINEAGES)))
    ax.set_yticklabels([n for n, _ in LINEAGES], fontsize=9.5)
    ax.set_xlabel("出生年", fontsize=12)
    ax.set_title("Figure 3. 音楽軸の文化選択肢空間 — 系統の出現/消滅と世代断絶",
                 fontsize=13, pad=12)

    # 断絶線: 1985/1990 と 1995/2000 のあいだ
    for boundary, label in [((1985, 1990), "断絶①\n掘る→流される"),
                            ((1995, 2000), "断絶②\nアイドル前提→TikTok前提")]:
        lo, hi = boundary
        if lo in years and hi in years:
            x = (years.index(lo) + years.index(hi)) / 2
            ax.axvline(x, color="#0b3d91", lw=2.2, ls="--", zorder=4)
            ax.text(x, -1.0, label, color="#0b3d91", fontsize=9.5,
                    ha="center", va="bottom")

    ax.set_xlim(-0.5, len(years) - 0.5)
    ax.set_ylim(len(LINEAGES) - 0.5, -1.6)
    ax.grid(False)
    fig.tight_layout()
    fig.savefig("fig3_music_disruption.png", dpi=200)
    plt.close(fig)
    print("[saved] fig3_music_disruption.png")


if __name__ == "__main__":
    figure2()
    figure3()
