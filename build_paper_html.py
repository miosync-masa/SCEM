#!/usr/bin/env python3
"""
build_paper_html.py — Markdown 論文を投稿体裁の単一 HTML へ変換する。

paper1.html と同じ方式:本文 Markdown を <script id="md" type="text/markdown"> に埋め込み、
ブラウザ側で marked.js が HTML 化、MathJax が数式を組版する(初回のみネット接続が必要)。
サーバ不要・単一ファイルで配布可能。画像は相対パス(../figures/...)のまま動く。

Usage:
    python3 build_paper_html.py --md docs/paper2_contextual_mode_resolver.md \
        --out docs/paper2.html --title "Contextual Mode Resolver — Paper 2"
"""
from __future__ import annotations
import argparse
from pathlib import Path

HEAD = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --ink:#1a1a1a; --rule:#ccc; }}
  html {{ font-size: 15px; }}
  body {{
    color: var(--ink);
    font-family: "Hiragino Mincho ProN", "Yu Mincho", serif;
    line-height: 1.8;
    max-width: 820px; margin: 0 auto; padding: 48px 32px 96px;
    text-align: justify;
  }}
  h1 {{ font-size: 1.7rem; line-height:1.4; font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }}
  h2 {{ font-size: 1.3rem; margin-top: 2.2em; border-bottom: 2px solid var(--ink); padding-bottom:.2em;
        font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }}
  h3 {{ font-size: 1.08rem; margin-top: 1.8em;
        font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }}
  p, li {{ font-size: 1rem; }}
  code {{ font-family: "SFMono-Regular", Menlo, monospace; font-size: .88em;
          background:#f3f3f3; padding:1px 4px; border-radius:3px; }}
  pre code {{ display:block; padding:10px; overflow-x:auto; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; font-size:.92rem; }}
  th, td {{ border: 1px solid var(--rule); padding: 6px 10px; text-align: left; }}
  th {{ background: #f3f3f3; }}
  img {{ max-width: 100%; height: auto; display:block; margin: 1em auto; }}
  hr {{ border:none; border-top:1px solid var(--rule); margin: 2em 0; }}
  blockquote {{ border-left: 4px solid #888; margin:1em 0; padding:.2em 1em; color:#333; background:#fafafa; }}
  a {{ color:#0b3d91; }}
  @media print {{
    body {{ max-width:none; padding:0; }}
    h2, h3 {{ page-break-after: avoid; }}
    table, img, blockquote, pre {{ page-break-inside: avoid; }}
    a {{ color: var(--ink); text-decoration:none; }}
    @page {{ margin: 18mm 16mm; }}
  }}
</style>
<script>
  window.MathJax = {{
    tex: {{ inlineMath: [['\\\\(','\\\\)']], displayMath: [['\\\\[','\\\\]']] }},
    svg: {{ fontCache: 'global' }}
  }};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" id="MathJax-script" async></script>
</head>
<body>
<div id="content">読み込み中…(初回はネット接続が必要)</div>
<script id="md" type="text/markdown">"""

TAIL = """</script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script>
  // 1) 数式を保護(marked が _ や * を誤変換するのを防ぐ)
  const raw = document.getElementById('md').textContent;
  const store = [];
  let protectedMd = raw
    .replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, (m,x)=>{ store.push('\\\\['+x+'\\\\]'); return '@@MJ'+(store.length-1)+'@@'; })
    .replace(/\\$([^\\$\\n]+?)\\$/g,       (m,x)=>{ store.push('\\\\('+x+'\\\\)'); return '@@MJ'+(store.length-1)+'@@'; });
  // 2) Markdown -> HTML
  marked.setOptions({ gfm:true, breaks:false });
  let out = marked.parse(protectedMd);
  // 3) 数式を復元
  out = out.replace(/@@MJ(\\d+)@@/g, (m,i)=>store[+i]);
  document.getElementById('content').innerHTML = out;
  // 4) MathJax 組版
  if (window.MathJax && window.MathJax.typesetPromise) window.MathJax.typesetPromise();
  else window.addEventListener('load', ()=> window.MathJax && window.MathJax.typesetPromise && window.MathJax.typesetPromise());
</script>
</body>
</html>
"""


def build(md_path: Path, out_path: Path, title: str):
    md = md_path.read_text(encoding="utf-8")
    # </script> がMarkdown本文に出ると埋め込みが壊れるので無害化(本文には通常出ない)
    md = md.replace("</script>", "<\\/script>")
    out_path.write_text(HEAD.format(title=title) + md + TAIL, encoding="utf-8")
    print(f"[built] {out_path}  ({len(md.splitlines())} md lines)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", required=True)
    args = ap.parse_args()
    here = Path(__file__).resolve().parent
    md = Path(args.md); md = md if md.is_absolute() else here / md
    out = Path(args.out); out = out if out.is_absolute() else here / out
    build(md, out, args.title)


if __name__ == "__main__":
    main()
