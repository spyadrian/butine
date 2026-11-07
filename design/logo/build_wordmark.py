"""Butine — logotype en tracés (Adwaita Sans = Inter, OFL 1.1), graisse 600, opsz 32.
Nécessite fontTools : python -m pip install fonttools.  Écrit wordmark-glyphs.json (tracés + chasses)."""
import json, os, sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/fonts/Adwaita/AdwaitaSans-Regular.ttf"
font = instantiateVariableFont(TTFont(SRC), {"wght": 600, "opsz": 32})
gs = font.getGlyphSet(); cmap = font.getBestCmap(); upm = font["head"].unitsPerEm
TEXT = "Butine"
TRACK = -0.012 * upm            # léger resserrage pour la taille d'affichage
x = 0; parts = []
for ch in TEXT:
    g = cmap[ord(ch)]
    pen = SVGPathPen(gs)
    gs[g].draw(TransformPen(pen, (1, 0, 0, -1, x, 0)))   # y vers le bas, ligne de base à 0
    bp = BoundsPen(gs); gs[g].draw(bp)
    parts.append({"ch": ch, "d": pen.getCommands(), "x": x, "adv": gs[g].width, "bounds": bp.bounds})
    x += gs[g].width + TRACK
os2 = font["OS/2"]
json.dump({"upm": upm, "cap": os2.sCapHeight, "xh": os2.sxHeight, "width": x - TRACK, "parts": parts},
          open(os.path.join(HERE, "wordmark-glyphs.json"), "w"))
print("cap", os2.sCapHeight, "xh", os2.sxHeight, "width", round(x - TRACK), [(p["ch"], p["d"].count("M")) for p in parts])
