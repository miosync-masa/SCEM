# GSS 二次分析 — 実装着手レポート(黒子 → 環・真道さま)

**版:** 0.1(2026-06-26) / **親:** `docs/`(Paper 2 GSS 実証設計 spec, 環 draft 0.1)
**状態:** spec §7 の「コア対比の開始点(確定)」まで実装・実行。**未決(6.3-6.6)は決め打ちしていない**(Non-overwrite)。

---

## 0. これは何

spec の「黒子へ実装引き継ぎ(GSS取得 → RELTRAD → セグメント構築 → コア対比)」を実行した記録。
**確定**項目のみ実装し、**未決**(検定統計量・period・多重比較)は曲線と N を出して判断材料にした。

実行物(`src/`):
- `gss_acquire.py` — GSS 1972–2024 Cumulative(Stata)取得 → 必要列 slim parquet 化(誰でも再取得可)
- `gss_segments.py` — CMR 8 共同体を GSS 変数の論理式で操作化(**GSS 公式 `reltrad` 使用、自作分類なし**)
- `gss_core_contrast.py` — コア対比(Coastal vs Bible Belt 同性婚 × 出生年コホート、**記述のみ**)

成果物:`figures/gss_core_contrast_ssm.png`、`data/gss_results/core_contrast_ssm.csv`。
生データ(570MB)は `data/gss/`(.gitignore)。`gss_acquire.py` で再生成。

---

## 1. データ実態(spec の前提と GSS 2024 release の食い違い・要共有)

実装中に判明した、**spec が想定した変数名と実ファイルのズレ**。いずれも回避済みだが設計に効く。

### 1.1 RELTRAD は移植不要 — **公式変数が同梱**
- spec §4.2 は「Burge の検証済み syntax を import、自作しない」。R は本環境に無い。
- だが **GSS cumulative に公式 `reltrad` 変数が同梱**(NORC/ARDA 計算、Steensland et al. 2000)。
  1=evangelical / 2=mainline / 3=black prot / 4=catholic / 5=jewish / 6=other faith / 7=nonaffiliated。
- → **移植も自作も不要**。公式変数をそのまま使用。`reltrad16`(16歳時)も利用可能。
- 注:**Mormon は reltrad では "other faith"(6)に吸収**されるため、`other`(具体宗派)コード
  {60 lds-mormon, 64 mormon, 162 reformed LDS}で別抽出(spec §4.2 の通り)。

### 1.2 9 区分の地理は `region` ではなく **`region_7222`**
- spec §4 は REGION(9区分: new england … pacific)を使う前提。
- **2024 release で `region` は 4 区分 census region に変更**(northeast/midwest/south/west)。
  9 区分は **`region_7222`** に退避し、**2022 までで打ち切り**(2024 は欠損)。
- → 地理ベースのセグメント(Coastal=NewEng/Pacific, Bible Belt=S.Atl/ESC/WSC 等)は **`region_7222`** を使用。
  代償として **2024 波は地理セグメントから落ちる**(態度変数自体は 2024 もあるが地理が無い)。

### 1.3 同性婚(旗艦)は **3 変数に分割** — 接続して 12 波
- spec §3.3 は「MARHOMO(〜2018/2021)と MARSAME(2021〜)の接続が必須」。実態はもう一段複雑:
  - `marsame` : 1988, 2004, 2021, 2022, 2024(N=8,583)
  - `marsame1`: 2006, 2008, 2010, 2012, 2014, 2016, 2018(N=10,973)← 旧 marhomo 波の本体
  - `marsamey`: 2024(N=1,070)
- 3 変数とも **1=strongly agree … 5=strongly disagree** の同一スケール。
- → 接続して **1988–2022 の 11 波**(地理あり)/ 2024 込みなら 12 波の時系列。`ssm_approve()` で実装。
  approve = code ∈ {1,2}。

### 1.4 `hispanic` は 2000 年以降のみ
- 白人セグメントで `hispanic==1`(非ヒス)を必須にすると **1988 など早期波が全消し**。
- → 白人 = `race==white` かつ(`hispanic` 欠損 or 非ヒス)= **2000 以前は race=white で近似**。
  これは構築上の選択(明示)。spec の「white 非ヒス」を早期波保持と両立させる近似。

---

## 2. コア対比(記述・unweighted): 同性婚 賛成率 × 出生年コホート

**Coastal Liberal(REFRAME 予測) vs Bible Belt(ACTIVE 予測)**。接続 11 波(1988–2022)。

**Coastal の薄 N 対処(真道さま決定 2026-06-26):案β+γ・graduate 維持・α却下。**
- **α(graduate→bachelor+)却下**:"graduate" は premise の弁別記号。緩めると Suburban MC と学歴軸で
  被る。N の都合で理論定義を上書き = Non-overwrite 違反に近い。**定義は graduate のまま維持**。
- **γ**:Coastal は「平坦高位(REFRAME 署名)」を**プール**で主張(細かい勾配は主張しない)。
- **β**:Coastal は **10 年刻み**で N を稼ぐ(平坦は粗くしても平坦)。Bible Belt は **5 年刻みで勾配**。
- 指摘#1(平坦は本物か薄Nのブレか)に答えるため **Wilson 95%CI** を付与(CI は誤差棒であって検定統計量ではない)。

![core contrast](../figures/gss_core_contrast_ssm.png)

| | marsame 非欠損 N | プール賛成率 [95%CI] | コホートの形 |
|---|---|---|---|
| **Coastal Liberal** | 116 | **91% [85%, 95%]** | **平坦高位**:10年ビンで 87–100%、CI 重なる=勾配なし |
| **Bible Belt** | 1,166 | **24% [21%, 26%]** | **明瞭な単調勾配**:~6–15%(–1944生)→ 42%(1985-89)→ 66%(1990-94) |

### 2.1 指摘#1への回答:平坦は本物(薄Nのブレではない)
- **Coastal プール 91%、CI[85,95%]** — N=116 でも CI は十分狭く「**高位**」と断言できる。10 年ビンでも
  1940-49〜1990-99 が 87–100% で CI が重なる = **平坦は本物**。薄 N でも γ(平坦高位)は成立。
- **Bible Belt** はプール 24% で、両端コホートの CI が非重複(例:1925-29 [2,18%] vs 1990-94 [47,80%])
  = **勾配は本物**。
- 2 共同体のプール CI([85,95%] vs [21,26%])は完全分離 → 対比は頑健。N 非対称は対比の妥当性を壊さない。

### 2.2 これは CMR 予測の向きと整合(記述+CI。検定は未実装)
- **Coastal = REFRAME 署名**:出生年に関わらず賛成が高位で平坦 = 「基準値が既に書き換わった共同体」。
  世代を追っても動く余地が小さい(天井近く)。
- **Bible Belt = ACTIVE/争点の前線**:出生年で賛成率が大きく動く = 共同体内に世代コントラスト。
  spec の polarization 検証が効くのはこちら。
- **双子検定の像**:片方が平坦高位・片方が勾配 = 単一 resolver が premise ごとに別モードへ解決した帰結
  (spec §5.1)。記述レベルでこの非対称が見えている。

> ⚠️ 「早期立ち上がり(shift)」「分散拡大(polarization)」の**検定統計量は未実装**(spec 6.3/6.4 未決)。
> CI は記述への誤差棒であって、その検定ではない。曲線の形と CI が予測と整合する以上の主張はまだしない
> (後付け防止 §5.2)。

### 2.3 主張スコープ決定(真道さま 2026-06-26):**b′ 抑制された2軸**

前提の修正(環の着弾):**Paper 1 は最初から Dynamic**(`着弾年齢`軸=非対称ガウス感受性窓・effective_year・
REFRAME発火は全て「いつ着弾したか」)。Paper 2 が足したのは `共同体premise`軸のみ。よって SCEM は
`作用モード = f(着弾年齢[Paper1], 共同体premise[Paper2])` の **元から2軸**。GSS の平坦 vs 勾配は、この
2軸が実データ上で交差した像。

採択スコープ = **b′(抑制された2軸)**:
- **実証する主張(一口サイズ維持)**:「**共同体の規範コードが、事象の出生年インプリントをゲートする**
  ——コードが抵抗する Bible Belt では着弾スロープが露出(急勾配)、抵抗が薄い Coastal では平坦化」
  = 共同体 × 出生年スロープの**交互作用(差分)**。
- **APC 地雷の回避(b′ の肝)**:両共同体は**同じ波(1988–2022)で観測** → 全体に効く period effect は
  共同体コントラストで差し引かれる(diff-in-diff)。「平坦 vs 勾配」の差は period では説明できない。
  ゆえに**機構(感受性窓 vs 世代交代)を分離せずとも、交互作用の差分は頑健に言える**。
- **言い切らないこと**:勾配の機構が「感受性窓そのもの」だとは主張しない(APC 未分離、spec §2.4)。
  Coastal の平坦も「共同体が摩擦を消した」と断定せず**天井効果の可能性**を併記。両方 Discussion 仮説。
- **却下**:full(b)=機構を言い切ると APC 地雷直撃+一口サイズ肥大 / (a)=データが見せる差分スロープを
  捨てる過少申告。
- **(c) は別件で Paper 3**:effective_year の時間発展(モード境界の暦年スライド)=唯一の本当に新しい軸。

→ 概念は「Paper1 年齢軸 + Paper2 共同体軸 = 2軸」を §2 で明示、実証主張は「共同体が出生年スロープを
ゲート」に絞る。これで Paper 1 と Paper 2 を **1本の GSS 実証で同時裏取り**しつつ一口サイズを保つ(C案統合と一致)。

---

## 3. 次セッションで決める論点(未決・決め打ちしない)

実データを見たうえで、判断材料込みで挙げる。**勝手に決めない**(Non-overwrite)。

1. ~~**Coastal の N 薄問題**~~ → **決着(2026-06-26):案β+γ・graduate 維持・α却下**(§2)。プール 91%
   [85,95%]・10 年ビンで平坦が CI 付きで確認でき、定義変更なしで解決。以降この方針で固定。
2. **6.3/6.4 の統計量(b′ で方向確定・値は未決)**:b′ 採択により、自然な主検定統計量の候補は
   **「共同体間の出生年スロープ差(community × cohort 交互作用)」**。Bible Belt 急 vs Coastal 平坦の
   スロープ差を 1 つの推定対象にする(diff-in-diff で period を差し引く)。具体の推定法(ロジ回帰の
   交互作用項 / スロープ比較 / 変化点)と、Coastal 天井効果の扱いは**次セッションで確定**(決め打ちしない)。
4. **6.5 period の扱い**:11 波を出生年へ畳む際の period 統制。今は unweighted・period 非分離。
5. **重み**:〜2018 `wtssall` / 2021+ `wtssps`・`wtssnrps`。波跨ぎ統合の weight 設計(現状 unweighted)。
6. **2024 波**:地理 `region_7222` が 2022 止まりのため地理セグメントから 2024 が落ちる。
   census 4 区分 `region` で 2024 を近似補完するか、2022 までで確定するか。

---

## 4. 再現

```bash
python3 src/gss_acquire.py          # GSS 取得 → data/gss/gss_slim.parquet(生データは .gitignore)
python3 src/gss_core_contrast.py    # コア対比(記述)→ figures/ + data/gss_results/
```

Paper 1/2 のコード・`events_patched.jsonl` は無改変。GSS 生データはリポジトリに含めない(NORC 無料公開)。
