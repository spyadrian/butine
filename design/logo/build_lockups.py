"""Butine — lockups horizontal, empilé et logotype seul, dans toutes les couleurs.
Lit palette.json et wordmark-glyphs.json (voir build_wordmark.py). Usage : python3 build_lockups.py"""
import json, os
from build_symbol import symbol_path
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "palette.json")))
W = json.load(open(os.path.join(HERE, "wordmark-glyphs.json")))
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
STD, REV = symbol_path(cy=130), symbol_path(cy=130, t=24.5, rd=16.5)
# Symbol visual box on its 256 canvas: x 35..221, y 25..233 (centre y ~129)
SX0, SX1, SY0, SY1 = 35.3, 220.7, 25, 232.8
CAP = 112                      # hauteur de capitale du logotype dans le lockup horizontal (≈ 0,54 × symbole)
GAP = 44                       # espace symbole–logotype ≈ 1,3 × diamètre du grain

def word(scale, x0, base, fill):
    paths = "".join(f'<path d="{p["d"]}" transform="translate({f(x0)} {f(base)}) scale({scale:.5f})"/>' for p in W["parts"])
    return f'<g id="logotype" fill="{fill}">{paths}</g>'

def sym(dx, dy, s, ring_fill, dot_fill, rev=False):
    r, d = REV if rev else STD
    return (f'<g id="symbole" transform="translate({f(dx)} {f(dy)}) scale({s})">'
            f'<path fill="{ring_fill}" d="{r}"/><path fill="{dot_fill}" d="{d}"/></g>')

def doc(w, h, body, title="Butine"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(w)} {f(h)}" width="{f(w)}" height="{f(h)}" role="img">'
            f'<title>{title}</title>{body}</svg>\n')

def horizontal(ring, dot, text, rev=False):
    s = CAP / W["cap"]
    lsb = W["parts"][0]["bounds"][0] * s
    x0 = SX1 + GAP - lsb
    base = (SY0 + SY1) / 2 + CAP / 2
    w = x0 + W["width"] * s + 24
    body = sym(-SX0 + 24, 0, 1, ring, dot, rev) + word(s, x0 - SX0 + 24, base, text)
    return doc(w - SX0 + 24, 256, body)

def stacked(ring, dot, text, rev=False):
    s = 78 / W["cap"]; ww = W["width"] * s
    w = max(ww, 256) + 48
    sx = (w - 256) / 2
    base = SY1 + 40 + 78
    return doc(w, base + 32, sym(sx, 0, 1, ring, dot, rev) + word(s, (w - ww) / 2, base, text))

def wordmark(text):
    s = 160 / W["cap"]; ww = W["width"] * s
    return doc(ww + 48, 256, word(s, 24, 128 + 80, text))

V = {  # nom : (anneau, grain, texte, version inversée ?)
  "anthracite": (P["anthracite"], P["anthracite"], P["anthracite"], False),
  "miel":       (P["anthracite"], P["honey_deep"], P["anthracite"], False),
  "inverse":    (P["offwhite"],   P["honey"],      P["offwhite"],   True),
  "noir":       ("#000", "#000", "#000", False),
  "blanc":      ("#FFF", "#FFF", "#FFF", True),
}
for name, (r, d, t, rev) in V.items():
    open(os.path.join(HERE, f"butine-horizontal-{name}.svg"), "w").write(horizontal(r, d, t, rev))
    open(os.path.join(HERE, f"butine-empile-{name}.svg"), "w").write(stacked(r, d, t, rev))
for name, col in (("anthracite", P["anthracite"]), ("inverse", P["offwhite"]), ("noir", "#000"), ("blanc", "#FFF")):
    open(os.path.join(HERE, f"butine-logotype-{name}.svg"), "w").write(wordmark(col))
print("ok")
