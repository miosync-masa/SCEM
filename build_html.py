"""
build_html.py — paper1_media_generation.md を印刷用の自己完結HTMLに変換する。
(pandoc/LaTeX不要。ブラウザで開いて Cmd+P → PDF保存 でSocArXiv用PDFが作れる)

- 数式: MathJax (CDN)、$...$ と $$...$$ を保護してからMarkdown変換
- 表: GFM (marked, CDN)
- 図: 相対パスのPNG(同ディレクトリ)をそのまま参照
- 日本語: システムフォント(明朝/ゴシック)

Run: python3 build_html.py   → paper1.html
注: 初回表示時のみCDN(marked/MathJax)取得のためネット接続が要る。
"""
import html as _html

SRC = "paper1_media_generation.md"
OUT = "paper1.html"

md = open(SRC, encoding="utf-8").read()

TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Situated Cohort Exposure Model (SCEM) — Paper 1</title>
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
<script id="md" type="text/markdown">{MD}</script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script>
  // 1) 数式を保護(marked が _ や * を誤変換するのを防ぐ)
  const raw = document.getElementById('md').textContent;
  const store = [];
  let protectedMd = raw
    .replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, (m,x)=>{{ store.push('\\\\['+x+'\\\\]'); return '@@MJ'+(store.length-1)+'@@'; }})
    .replace(/\\$([^\\$\\n]+?)\\$/g,       (m,x)=>{{ store.push('\\\\('+x+'\\\\)'); return '@@MJ'+(store.length-1)+'@@'; }});
  // 2) Markdown -> HTML
  marked.setOptions({{ gfm:true, breaks:false }});
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

# <script>内に素の </script> が無いことを確認(あれば壊れる)
assert "</script>" not in md, "md に </script> が含まれています"

open(OUT, "w", encoding="utf-8").write(TEMPLATE.format(MD=md))
print(f"[saved] {OUT}  (ブラウザで開く → Cmd+P → PDFとして保存)")
