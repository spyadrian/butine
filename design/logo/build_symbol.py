"""Butine — Alvéole ouverte. Construit le symbole en tracé plein (pas de stroke).
Hexagone à pointe en haut, côté haut-droit ouvert ; le grain (point) se pose au milieu du côté ouvert.
Usage : python3 build_symbol.py  -> écrit symbol-*.svg dans ce dossier."""
import math, os
HERE = os.path.dirname(os.path.abspath(__file__))
f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")

def symbol_path(cx=128, cy=128, Rm=92, t=26, rc=14, rd=17, dot_out=0, trim=0):
    h = t / 2
    V = lambda k: (cx + Rm*math.cos(math.radians(-90+60*k)), cy + Rm*math.sin(math.radians(-90+60*k)))
    N = lambda k: (math.cos(math.radians(-60+60*k)), math.sin(math.radians(-60+60*k)))  # outward normal of edge k (Vk->Vk+1)
    def C(k):  # centre of the rounded corner at vertex k
        d = rc / math.cos(math.radians(30)); u = (math.cos(math.radians(-90+60*k)), math.sin(math.radians(-90+60*k)))
        x, y = V(k); return (x - d*u[0], y - d*u[1])
    add = lambda p, n, s: (p[0] + s*n[0], p[1] + s*n[1])
    # open polyline V1 -> V2 -> V3 -> V4 -> V5 -> V0 ; edges 1..5 ; rounded corners at 2..5 ; caps at V1, V0
    ro, ri = rc + h, rc - h
    def toward(p, q, e):
        L = math.dist(p, q); return (p[0] + (q[0]-p[0])*e/L, p[1] + (q[1]-p[1])*e/L)
    E1, E0 = toward(V(1), V(2), trim), toward(V(0), V(5), trim)   # ends of the open stroke
    d = [f"M{f(add(E1, N(1), h)[0])} {f(add(E1, N(1), h)[1])}"]
    for k in (2, 3, 4, 5):            # outer side, clockwise
        a = add(C(k), N(k-1), ro); b = add(C(k), N(k), ro)
        d.append(f"L{f(a[0])} {f(a[1])} A{f(ro)} {f(ro)} 0 0 1 {f(b[0])} {f(b[1])}")
    e = add(E0, N(5), h); d.append(f"L{f(e[0])} {f(e[1])}")
    e2 = add(E0, N(5), -h); d.append(f"A{f(h)} {f(h)} 0 0 1 {f(e2[0])} {f(e2[1])}")   # cap at V0
    for k in (5, 4, 3, 2):            # inner side, back
        a = add(C(k), N(k), ri); b = add(C(k), N(k-1), ri)
        d.append(f"L{f(a[0])} {f(a[1])} A{f(abs(ri))} {f(abs(ri))} 0 0 0 {f(b[0])} {f(b[1])}")
    s = add(E1, N(1), -h); d.append(f"L{f(s[0])} {f(s[1])}")
    s2 = add(E1, N(1), h); d.append(f"A{f(h)} {f(h)} 0 0 1 {f(s2[0])} {f(s2[1])} Z")
    ring = " ".join(d)
    m = ((V(0)[0]+V(1)[0])/2, (V(0)[1]+V(1)[1])/2); n0 = N(0)
    dc = (m[0]+dot_out*n0[0], m[1]+dot_out*n0[1])
    dot = f"M{f(dc[0]-rd)} {f(dc[1])} A{rd} {rd} 0 1 0 {f(dc[0]+rd)} {f(dc[1])} A{rd} {rd} 0 1 0 {f(dc[0]-rd)} {f(dc[1])} Z"
    return ring, dot

def svg(ring, dot, ring_fill, dot_fill, bg=None, title="Butine"):
    b = f'<rect width="256" height="256" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img">'
            f'<title>{title}</title>{b}<path id="alveole" fill="{ring_fill}" d="{ring}"/><path id="grain" fill="{dot_fill}" d="{dot}"/></svg>\n')

if __name__ == "__main__":
    import json
    P = json.load(open(os.path.join(HERE, "palette.json")))
    std = symbol_path(cy=130)                                   # optical: a hair below centre, the dot adds weight top-right
    small = symbol_path(cy=130, Rm=90, t=34, rc=12, rd=19, dot_out=10)   # small-size cut (<= 32 px)
    tiny = symbol_path(cy=132, Rm=84, t=40, rc=8, rd=26, dot_out=14, trim=30)   # 16 px cut: shorter ends, bigger grain
    rev = symbol_path(cy=130, t=24.5, rd=16.5)                  # reversed: slightly thinner, light on dark looks bolder
    out = {
      "symbol-black.svg": svg(*std, "#000", "#000"),
      "symbol-anthracite.svg": svg(*std, P["anthracite"], P["anthracite"]),
      "symbol-honey-dot.svg": svg(*std, P["anthracite"], P["honey_deep"]),
      "symbol-reversed.svg": svg(*rev, P["offwhite"], P["honey"]),
      "symbol-white.svg": svg(*rev, "#FFFFFF", "#FFFFFF"),
      "symbol-small.svg": svg(*small, P["anthracite"], P["anthracite"]),
      "symbol-tiny.svg": svg(*tiny, P["anthracite"], P["anthracite"]),
    }
    for n, s in out.items(): open(os.path.join(HERE, n), "w").write(s)
    print("wrote", ", ".join(out))
