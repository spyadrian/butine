"""Butine — planche « Lockups & couleurs » (SVG + PNG). Usage : python3 build_sheet.py"""
import json, os, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "palette.json")))
FONT = "Adwaita Sans, Inter, sans-serif"

def art(fn, x, y, w=None, h=None):
    s = open(os.path.join(HERE, fn)).read()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1); vw, vh = map(float, vb.split()[2:])
    inner = re.sub(r"<title>.*?</title>", "", re.search(r"<svg[^>]*>(.*)</svg>", s, re.S).group(1), flags=re.S)
    if w and not h: h = w * vh / vw
    if h and not w: w = h * vw / vh
    return f'<svg x="{x}" y="{y}" width="{w:.1f}" height="{h:.1f}" viewBox="{vb}">{inner}</svg>', w, h

def card(x, y, w, h, bg, label, dark=False, border=False):
    st = ' stroke="#E6E0D6"' if border else ""
    col = P["grey_dark"] if dark else (P["anthracite"] if bg == P["honey"] else P["grey_light"])
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{bg}"{st}/>'
            f'<text x="{x+20}" y="{y+h-18}" font-family="{FONT}" font-size="13" fill="{col}">{label}</text>')

def centred(fn, x, y, w, h, aw=None, ah=None):
    a, ww, hh = art(fn, 0, 0, aw, ah)
    return art(fn, x + (w - ww) / 2, y + (h - hh) / 2 - 10, aw, ah)[0]

W = 1600; out = []
T = lambda x, y, s, size=14, col=P["anthracite"], wt=400: f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{wt}" fill="{col}">{s}</text>'
out.append(T(64, 76, "LOCKUPS &amp; COULEURS", 13, P["grey_light"], 500))
out.append(T(64, 120, "Butine — alvéole ouverte", 36, P["anthracite"], 700))
# Row 1: horizontal lockup on the three backgrounds
y = 160; cw, ch = (W - 128 - 48) / 3, 220
for i, (bg, fn, lab, dk) in enumerate([(P["offwhite"], "butine-horizontal-anthracite.svg", "Horizontal · anthracite sur blanc cassé", 0),
                                        (P["night"], "butine-horizontal-inverse.svg", "Horizontal · inversé sur nuit", 1),
                                        (P["honey"], "butine-horizontal-anthracite.svg", "Horizontal · anthracite sur miel", 0)]):
    x = 64 + i * (cw + 24); out.append(card(x, y, cw, ch, bg, lab, dk, bg == P["offwhite"])); out.append(centred(fn, x, y, cw, ch, aw=340))
# Row 2: stacked, symbol, wordmark, small sizes
y = 404; ch = 260; cw4 = (W - 128 - 3 * 24) / 4
items = [(P["offwhite"], "butine-empile-anthracite.svg", "Empilé · écran de démarrage, stores", 0, dict(ah=190)),
         (P["night"], "butine-empile-inverse.svg", "Empilé · inversé", 1, dict(ah=190)),
         (P["offwhite"], "butine-logotype-anthracite.svg", "Logotype seul", 0, dict(aw=250)),
         (P["offwhite"], "symbol-honey-dot.svg", "Symbole · grain miel profond (grand format)", 0, dict(ah=170))]
for i, (bg, fn, lab, dk, kw) in enumerate(items):
    x = 64 + i * (cw4 + 24); out.append(card(x, y, cw4, ch, bg, lab, dk, bg == P["offwhite"])); out.append(centred(fn, x, y, cw4, ch, **kw))
# Row 3: one-colour + size ladder
y = 688; ch = 170
x = 64; out.append(card(x, y, 360, ch, "#FFFFFF", "Une couleur · noir", 0, True)); out.append(centred("butine-horizontal-noir.svg", x, y, 360, ch, aw=260))
x = 448; out.append(card(x, y, 360, ch, "#000000", "Une couleur · blanc", 1)); out.append(centred("butine-horizontal-blanc.svg", x, y, 360, ch, aw=260))
x = 832; out.append(card(x, y, W - 64 - 832, ch, P["offwhite"], "Coupes par taille · standard 64 / 48 px · small 32 / 24 px · tiny 16 px", 0, True))
cx = x + 40
for fn, s in (("symbol-anthracite.svg", 64), ("symbol-anthracite.svg", 48), ("symbol-small.svg", 32), ("symbol-small.svg", 24), ("symbol-tiny.svg", 16)):
    out.append(art(fn, cx, y + 70 - s / 2, s, s)[0]); cx += s + 40
# Row 4: palette
y = 882; out.append(T(64, y + 20, "Palette", 20, P["anthracite"], 700))
sw = [("Miel", "honey", "anthracite dessus 7,6:1"), ("Miel profond", "honey_deep", "graphique sur clair 3,4:1"),
      ("Anthracite", "anthracite", "sur blanc cassé 14,0:1"), ("Blanc cassé", "offwhite", "fond clair"),
      ("Nuit", "night", "fond sombre · texte 16,4:1"), ("Gris chaud clair", "grey_light", "sur blanc cassé 4,8:1"),
      ("Gris chaud sombre", "grey_dark", "sur nuit 6,4:1"), ("Erreur", "error", "sur blanc cassé 6,0:1"),
      ("Erreur · sombre", "error_dark", "sur nuit 6,6:1")]
sww = (W - 128 - 8 * 16) / 9
for i, (n, k, note) in enumerate(sw):
    x = 64 + i * (sww + 16); y0 = y + 40
    out.append(f'<rect x="{x}" y="{y0}" width="{sww:.1f}" height="90" rx="12" fill="{P[k]}" stroke="#E6E0D6"/>')
    out.append(T(x, y0 + 114, n, 14, P["anthracite"], 600)); out.append(T(x, y0 + 134, P[k], 13, P["grey_light"]))
    out.append(T(x, y0 + 152, note, 11, P["grey_light"]))
# Row 5: error in use (light + dark) next to the honey signal
y = 1112
def ui(x, bg, fg, err, tint, honey_ok, dark):
    s = [f'<rect x="{x}" y="{y}" width="728" height="150" rx="16" fill="{bg}"{"" if dark else " stroke=\"#E6E0D6\""}/>']
    s.append(f'<rect x="{x+24}" y="{y+24}" width="420" height="52" rx="10" fill="{tint}"/>')
    s.append(f'<circle cx="{x+50}" cy="{y+50}" r="10" fill="none" stroke="{err}" stroke-width="2.5"/><rect x="{x+48.75}" y="{y+43}" width="2.5" height="9" rx="1" fill="{err}"/><circle cx="{x+50}" cy="{y+56}" r="1.5" fill="{err}"/>')
    s.append(T(x + 72, y + 55, "Impossible de récupérer les papiers. Réessaie.", 14, err, 600))
    s.append(f'<rect x="{x+24}" y="{y+92}" width="170" height="40" rx="20" fill="{P["honey"]}"/>' + T(x + 52, y + 117, "Créer un prompt", 14, P["anthracite"], 600))
    s.append(f'<circle cx="{x+230}" cy="{y+112}" r="6" fill="{P["honey"] if honey_ok else P["honey_deep"]}"/>' + T(x + 244, y + 117, "3 nouveaux papiers", 14, fg))
    s.append(T(x + 470, y + 55, "Erreur : grenat + icône + texte", 12, P["grey_dark"] if dark else P["grey_light"]))
    s.append(T(x + 470, y + 75, "jamais la couleur seule", 12, P["grey_dark"] if dark else P["grey_light"]))
    s.append(T(x + 470, y + 117, "Signal : miel, rare", 12, P["grey_dark"] if dark else P["grey_light"]))
    return "".join(s)
out.append(ui(64, P["offwhite"], P["anthracite"], P["error"], P["error_tint"], False, False))
out.append(ui(808, P["night"], P["offwhite"], P["error_dark"], P["error_tint_dark"], True, True))
out.append(T(64, 1310, "Butine — lockups &amp; couleurs", 12, P["grey_light"]))
H = 1340
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
       f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>{"".join(out)}</svg>\n')
open(os.path.join(HERE, "presentation", "lockups-couleurs.svg"), "w").write(svg)
subprocess.run(["rsvg-convert", "-w", str(W), os.path.join(HERE, "presentation", "lockups-couleurs.svg"),
                "-o", os.path.join(HERE, "presentation", "lockups-couleurs.png")], check=True)
print("wrote presentation/lockups-couleurs.svg/.png")
