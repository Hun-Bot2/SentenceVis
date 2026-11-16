"""Expand docs/specs/glyph_registry.json into concrete SVG glyphs.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/checks/glyphs.py check-html OUT.html   # pixel distinctness test page
      (fixed scale: 20 glyph units = 12px, as on screen; canvas covers -3..29 units so
       marks drawn outside the glyph cell, such as '=', are measured at real size)
    python3 scripts/checks/glyphs.py legend OUT.svg        # final legend preview
    python3 scripts/checks/glyphs.py ts OUT.ts             # generated TypeScript glyph table for src/vis
Template tokens: C = ink, F = fill (none / ink), W = stroke width (thin / thick),
BG = background, '@name+' = include another glyph, '@name:filled+' = include it filled.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = json.loads((ROOT / "docs/specs/glyph_registry.json").read_text())["glyphs"]
THICK = {"not_scalar": 2.4, "not_applicable": 2.6, "not_extracted": 2.6}


def expand(name: str, second: bool, ink: str = "#000", bg: str = "#fff") -> str:
    g = REG[name]
    s = g["svg"]
    m = re.match(r"@(\w+)@scale([\d.]+)@at(-?[\d.]+),(-?[\d.]+)$", s)
    if m:  # small modifier icon
        inner = expand(m.group(1), False, ink, bg)
        return f"<g transform='translate({m.group(3)} {m.group(4)}) scale({m.group(2)})'>{inner}</g>"
    m = re.match(r"@(\w+)(:filled)?\+(.*)$", s, re.S)
    prefix = ""
    if m:
        prefix = expand(m.group(1), bool(m.group(2)) or second, ink, bg)
        s = m.group(3)
    fv = g["fill_variant"]
    fill = ink if (second and fv in ("pans", "pans_heavy", "dot", "doc")) else "none"
    knock = bg if (second and fv == "doc") else ink  # 'K': lines drawn inside a filled shape
    width = str(THICK.get(name, 2.4) if (second and fv in ("stroke", "pans_heavy")) else 1.4)
    s = s.replace("'C'", f"'{ink}'").replace("'F'", f"'{fill}'").replace("'W'", f"'{width}'").replace("'BG'", f"'{bg}'").replace("'K'", f"'{knock}'")
    return prefix + s


def variants():
    for name, g in REG.items():
        if name == "appeal_not_final":
            continue
        if g["fill_variant"] == "none":
            yield f"{name}", expand(name, False)
        else:
            yield f"{name}/1심", expand(name, False)
            yield f"{name}/2심", expand(name, True)


def check_html(out: str) -> None:
    items = [{"id": k, "svg": v} for k, v in variants()]
    page = """<!doctype html><meta charset="utf-8"><title>Glyph distinctness</title>
<body><pre id="out">running…</pre><script>
const ITEMS=%s, UNIT=12/20, VB=[-3,-2,32,24], CW=Math.round(VB[2]*UNIT), CH=Math.round(VB[3]*UNIT);
function ink(svg){return new Promise(res=>{const img=new Image();
 img.onload=()=>{const c=document.createElement('canvas');c.width=CW;c.height=CH;const x=c.getContext('2d');
  x.fillStyle='#fff';x.fillRect(0,0,CW,CH);x.drawImage(img,0,0,CW,CH);
  const d=x.getImageData(0,0,CW,CH).data;const v=[];for(let i=0;i<d.length;i+=4)v.push(255-(d[i]+d[i+1]+d[i+2])/3);res(v);};
 img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="${CW}" height="${CH}" viewBox="${VB.join(' ')}">${svg}</svg>`);});}
(async()=>{const V=[];for(const it of ITEMS)V.push(await ink(it.svg));
 const sim=(a,b)=>{let n=0,d=0;for(let i=0;i<a.length;i++){n+=Math.min(a[i],b[i]);d+=Math.max(a[i],b[i]);}return d?n/d:1;};
 const pairs=[];for(let i=0;i<V.length;i++)for(let j=i+1;j<V.length;j++)pairs.push([sim(V[i],V[j]),ITEMS[i].id,ITEMS[j].id]);
 pairs.sort((a,b)=>b[0]-a[0]);window.RESULT={n:ITEMS.length,top:pairs.slice(0,12).map(p=>[+p[0].toFixed(3),p[1],p[2]]),
  pairs_over_0_6:pairs.filter(p=>p[0]>0.6).length};
 document.getElementById('out').textContent=JSON.stringify(window.RESULT,null,1);})();
</script>""" % json.dumps(items, ensure_ascii=False)
    Path(out).write_text(page)


def legend(out: str) -> None:
    rows = []
    y = 34
    for name, g in REG.items():
        if g["fill_variant"] == "none":
            cells = [(20, 12, False), (62, 24, False)]
        else:
            cells = [(20, 12, False), (38, 12, True), (62, 24, False), (92, 24, True)]
        if name == "appeal_not_final":
            body = expand("observed", True) + expand(name, False)  # small mark above the 2심 glyph
            cells = [(20, 12, None), (62, 24, None)]
        for x, s, sec in cells:
            inner = body if sec is None else expand(name, sec)
            rows.append(f'<svg x="{x}" y="{y - s / 2}" width="{s}" height="{s}" viewBox="0 0 20 20" overflow="visible">{inner}</svg>')
        who = "사용자" if g["decided_by"] == "user" else "Claude(위임)"
        rows.append(f'<text x="130" y="{y + 4}" font-size="12" font-family="sans-serif" fill="#111">{g["label"]}</text>'
                    f'<text x="520" y="{y + 4}" font-size="10" font-family="sans-serif" fill="#777">{who}</text>')
        y += 34
    for months in (24, 120, 240):  # dumbbell width = 1 + 5 * max(months) / 240 (registry 'lines.dumbbell')
        w = 1 + 5 * months / 240
        rows.append(f'<line x1="20" y1="{y}" x2="110" y2="{y}" stroke="#000" stroke-width="{w:.2f}"/>'
                    f'<text x="130" y="{y + 4}" font-size="12" font-family="sans-serif" fill="#111">1심 → 2심 선 · 큰 쪽 {months}개월</text>')
        y += 24
    for label, dash in (("축 위 점 ↔ 축 바깥 칸", "4 2"), ("대법원 자료 없음", "gap")):
        if dash == "gap":
            line = f'<line x1="20" y1="{y}" x2="70" y2="{y}" stroke="#000"/><line x1="78" y1="{y}" x2="110" y2="{y}" stroke="#000" stroke-dasharray="1 3"/>'
        else:
            line = f'<line x1="20" y1="{y}" x2="110" y2="{y}" stroke="#000"{f" stroke-dasharray=\"{dash}\"" if dash else ""}/>'
        rows.append(line + f'<text x="130" y="{y + 4}" font-size="12" font-family="sans-serif" fill="#111">{label}</text>')
        y += 28
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="{y + 10}" viewBox="0 0 600 {y + 10}">'
           f'<rect width="100%" height="100%" fill="#fff"/><text x="20" y="16" font-size="11" font-family="sans-serif" fill="#666">'
           f'SentenScope V1 범례 초안 · 1심(빈/가는) · 2심(채운/굵은) · 2배</text>{"".join(rows)}</svg>')
    Path(out).write_text(svg)


def ts(out: str) -> None:
    table = {}
    for name, g in REG.items():
        table[name] = {"label": g["label"],
                       "first": expand(name, False, "currentColor", "var(--bg)"),
                       "second": expand(name, True, "currentColor", "var(--bg)")}
    body = json.dumps(table, ensure_ascii=False, indent=1)
    Path(out).write_text("// GENERATED by scripts/checks/glyphs.py from docs/specs/glyph_registry.json. Do not edit.\n"
                         "// AI-assisted (Claude Code, 2026-11-16).\n"
                         "export interface GlyphDef { label: string; first: string; second: string }\n"
                         f"export const GLYPHS: Record<string, GlyphDef> = {body};\n")


if __name__ == "__main__":
    cmd, out = sys.argv[1], sys.argv[2]
    {"check-html": check_html, "legend": legend, "ts": ts}[cmd](out)
