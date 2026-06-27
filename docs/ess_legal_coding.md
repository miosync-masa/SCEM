# ESS effective_year — LGBT 制度モーメント年 コーディング表(出典付き)

**用途:** `src/ess_effective_year.py` の `LEGAL` 辞書の出典。findings §2.2(ρ=+0.41/+0.54)の制度年の根拠。
**検証(2026-06-27):** 各国の年を Wikipedia *"Recognition of same-sex unions in Europe"*(各国の**国内立法を脚注で引用**)
+ ILGA-Europe(Rainbow Map / Annual Review)で横断確認。**主要アンカー国は国内法を明記**(下表「primary law」)。
**強度:** 制度年 = **事象の着弾年**であって個人の mode ではない。年の付与は外部照合用。論文最終版では
ILGA-Europe Rainbow Map と各国官報を一次として最終確認する(本表はそれに足る精度で固めた)。

---

## コーディング規則

- **recognition_year** = 同性カップルへの**最初の実質的・全国的な法的地位**(登録パートナーシップ/シビルユニオン、
  無ければ婚姻)。地域限定パートナーシップ・限定的 de facto 認知は採らない(下記「定義選択」参照)。
- **ssm_year** = 同性婚合法化の発効年(感度分析用)。
- 2024 年時点で制度なし = `None`(分析では sentinel 2030 = 「very late / not yet」)。

## 表(ESS 分析対象国)

| 国 | recognition_year | ssm_year | 種別(最初の地位) | primary law / 出典 |
|---|---|---|---|---|
| DK | 1989 | 2012 | 登録パートナー(世界初) | Registered Partnership Act 1989 |
| NO | 1993 | 2009 | 登録パートナー | Joint Household Act / Partnership Act 1993 |
| SE | 1995 | 2009 | 登録パートナー | Registered Partnership Act 1994(発効1995) |
| IS | 1996 | 2010 | 登録パートナー(確認同居) | Confirmed Cohabitation Act 1996 |
| NL | 1998 | 2001 | 登録パートナー | Registered Partnership 1998 / Opening up of Marriage Act 2001 |
| FR | 1999 | 2013 | PACS | Loi n° 99-944(PACS)/ Loi n° 2013-404(婚姻) |
| BE | 2000 | 2003 | 法的同居 | Cohabitation légale 2000 / 婚姻法 2003 |
| DE | 2001 | 2017 | 生活パートナー | Lebenspartnerschaftsgesetz 2001 / Ehe für alle 2017 |
| FI | 2002 | 2017 | 登録パートナー | Registered Partnership Act 2002 |
| GB | 2005 | 2014 | シビルパートナー | Civil Partnership Act 2004(発効2005)/ M(SSC) Act 2013(発効2014) |
| ES | 2005 | 2005 | 婚姻 | **Ley 13/2005** |
| CZ | 2006 | None | 登録パートナー | Registered Partnership Act 2006 |
| SI | 2006 | 2022 | 登録パートナー | 2006 / 婚姻 2022 |
| CH | 2007 | 2022 | 登録パートナー | Partnership Act 2007 / Marriage for All 2022 |
| HU | 2009 | None | 登録パートナー | Registered Partnership Act 2009(※未登録同居 1996=下記定義選択) |
| AT | 2010 | 2019 | 登録パートナー | Eingetragene Partnerschaft 2010 / 婚姻 2019 |
| PT | 2010 | 2010 | 婚姻 | **Lei n.º 9/2010**(※de facto union 2001=定義選択) |
| IE | 2011 | 2015 | シビルパートナー | Civil Partnership Act 2010(発効2011)/ **Marriage Act 2015** |
| HR | 2014 | None | 生活パートナー | Life Partnership Act 2014 |
| CY | 2015 | None | シビルユニオン | Civil Union Law 2015 |
| GR | 2015 | 2024 | シビルユニオン | **Law 4356/2015**(同棲協定)/ **Law 5089/2024**(婚姻) |
| IT | 2016 | None | シビルユニオン | **Law 76/2016(Cirinnà)** |
| EE | 2016 | 2024 | 登録パートナー | Registered Partnership Act 2014(発効2016)/ 婚姻 2024 |
| ME | 2021 | None | 生活パートナー | Life Partnership Law 2021 |
| LV | 2024 | None | 登録パートナー | 2024 |
| IL | None | None | 国内制度なし(外国婚姻を一部承認) | — |
| PL / LT / SK / BG / RS / MK / RU | None | None | 制度なし(2024時点) | — |

> LT は 2024–25 にパートナーシップ法案の動きがあるが、ESS 観測期間(2014–2024)では制度なし扱い。

---

## 定義選択(残る判断・感度で確認済)

操作化に幅がある国を明示する。**いずれも recognition / marriage 両版で同符号 → 結論は頑健**:

- **NL**:登録パートナー 1998(採用)vs 婚姻 2001。
- **PT**:婚姻 2010(採用)vs de facto union(união de facto)2001(限定的)。
- **BE**:法的同居 2000(採用、限定的)vs 婚姻 2003。
- **HU**:登録パートナー 2009(採用)vs 未登録同居の判例認知 1996。
- **IS**:確認同居 1996(採用)。分析では飽和で除外。

**感度分析(`ess_effective_year.py`)**:effective_year を recognition_year ではなく **ssm_year(婚姻年)** にしても
Spearman は同符号(スロープ z: +0.41→**+0.34** / 変化点出生年: +0.54→**+0.67**)。
→ **パートナー年 vs 婚姻年の操作化選択に対して頑健**。「遅い国ほど移行が若い出生年に寄る」は婚姻年版で更に強い(+0.67)。

---

## 出典(論文化時の citation)

1. Wikipedia, *Recognition of same-sex unions in Europe*(各国の国内立法を脚注で引用)— 横断確認に使用。
2. ILGA-Europe, *Annual Review / Rainbow Europe Map*(europa の各国法的状況の権威ある年次コンパイル)。
3. アンカー国は国内法を明記(ES Ley 13/2005 / PT Lei 9/2010 / IT Law 76/2016 Cirinnà / GR Law 4356/2015・5089/2024 /
   IE Marriage Act 2015 / 等)。
4. (任意)Pew Research, *Same-Sex Marriage Around the World*(婚姻年の横断確認)。

> 最終投稿前チェック:本表を ILGA-Europe Rainbow Map の最新版と各国官報で 1 国ずつ突合(本表はその精度で固めた)。
