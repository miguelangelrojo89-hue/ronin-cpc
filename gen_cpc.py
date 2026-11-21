# Genera data.h para el port a Amstrad CPC (Mode 1: 320x200, 4 plumas, 4 pixeles por byte).
# Reutiliza sprites, fuente y niveles del port de QL (assets.py, levels.py).
#
# Formato Mode 1: un byte = 4 pixeles. Pixel p (0 = izquierda): bit (7-p) = bit0 de la pluma,
#                 bit (3-p) = bit1 de la pluma.
# Plumas: 0 negro | 1 blanco | 2 color del tema (cambia por nivel) | 3 amarillo
import assets as A
import levels
from cjk_data import CJK

# --- correspondencia caracter de sprite -> pluma -------------------------------------------
BASE = {'X': 3, 'W': 1, 'B': 2, 'R': 2, 'K': 0, 'Y': 3, 'G': 1, 'C': 1, 'M': 2}

def table(**over):
    t = dict(BASE); t.update(over); return t

PLAYER = table()                                    # casco amarillo, cuerpo blanco, pecho/piernas del tema
def enemy_table(v):                                 # dos variantes de casco (4 sombreros en QL -> 2 aqui)
    hat = (2, 1)[v]
    return table(X=hat, B=hat, W=3, R=2)

def pack_row(row, flip, tb, opaque_dots):
    d = m = 0
    out_d = []; out_m = []
    for h in range(2):
        bd = bm = 0
        for k in range(4):
            sx = h * 4 + k
            ch = row[7 - sx if flip else sx]
            if ch == '.':
                if not opaque_dots: continue
                pen, msk = 0, 1
            else:
                pen, msk = tb[ch], 1
            if msk: bm |= (0x80 >> k) | (0x08 >> k)
            if pen & 1: bd |= 0x80 >> k
            if pen & 2: bd |= 0x08 >> k
        out_d.append(bd); out_m.append(bm)
    return out_d, out_m

def pack_sprite(rows, flip, tb, opaque_dots=False):
    D = []; M = []
    for r in rows:
        d, m = pack_row(r, flip, tb, opaque_dots)
        D += d; M += m
    return D, M

# --- niveles (mismo procesado que gen.py del QL) -------------------------------------------
EXITROW = " " * 25 + "abc"
LEVEL, LEVEL2 = A.LEVEL, A.LEVEL2
for L in (LEVEL, LEVEL2):
    L[0] = EXITROW; r = L[1].ljust(28); assert r[25] == ' ' and r[27] == 'D'; L[1] = r[:25] + 'p' + r[26:]
LV = [levels.rows(f()) for f in (levels.level3, levels.level4, levels.level5, levels.level6, levels.level7,
      levels.level8, levels.level9, levels.level10, levels.level11, levels.level12, levels.level13,
      levels.level14, levels.level15, levels.level16, levels.level17, levels.level18, levels.level19)]
ALL = []; KEYS = []
for L in [LEVEL, LEVEL2] + LV:
    rr, pos, det = levels.add_key(L); ALL.append(rr); KEYS.append((pos, det))

def arr(name, vals, typ="u8"):
    return "static const %s %s[%d]={%s};" % (typ, name, len(vals), ",".join(str(v) for v in vals))

o = ["/* generado por gen_cpc.py -- no editar a mano */"]
o.append("static const char LEVELS[19][15][29]={" + ",".join(
    "{" + ",".join('"' + r.ljust(28) + '"' for r in L) + "}" for L in ALL) + "};")

# jugador: 5 poses x 2 volteos
pld = []; plm = []
for i in range(5):
    for f in range(2):
        d, m = pack_sprite(A.S[A.order[i]], f, PLAYER); pld += d; plm += m
o.append(arr("PLD", pld)); o.append(arr("PLM", plm))
# enemigos: 4 poses x 2 variantes x 2 volteos
end = []; enm = []
for i in range(4):
    for v in range(2):
        for f in range(2):
            d, m = pack_sprite(A.S[A.order[i]], f, enemy_table(v)); end += d; enm += m
o.append(arr("END", end)); o.append(arr("ENM", enm))
# baldosas (17, opacas)
til = []
names = A.order[5:22]
for k in names:
    over = {}
    if k.startswith('sign'): over = {'G': 2}          # cartel EXIT: fondo del color del tema
    if k == 'doorO': over = {'G': 0}                  # puerta abierta: interior oscuro
    tb = table(**over)
    d, m = pack_sprite(A.S[k], 0, tb, opaque_dots=True); til += d
assert len(names) == 17 and len(til) == 17 * 24
o.append(arr("TILES", til))
# fuente 3x5
o.append('static const char FONT_CH[]="%s";' % ''.join(A.FONT))
o.append(arr("FONT_BITS", [int(v, 2) for v in A.FONT.values()], "u16"))
# kanji 24x24
o.append("static const u8 CJK[7][72]={" + ",".join("{" + ",".join(map(str, r)) + "}" for r in CJK) + "};")
open('data.h', 'w').write("\n".join(o) + "\n")
print("data.h ok:", len("\n".join(o)), "bytes de fuente; niveles:", len(ALL))
