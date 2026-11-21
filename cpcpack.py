"""Utilidades para Amstrad CPC: Intel HEX -> binario, cabecera AMSDOS y creacion de imagenes .dsk.

Formato de disco generado: DSK estandar ("MV - CPCEMU"), 40 pistas, 1 cara, 9 sectores de 512 bytes
(IDs &C1-&C9), formato de datos de CP/M de AMSDOS: bloques de 1 KB, 64 entradas de directorio, sin pistas
reservadas. Es el formato que lee cualquier CPC (464+DDI-1, 664, 6128) y los emuladores.
"""
import struct

# ---------------------------------------------------------------- Intel HEX
def ihx_to_image(text):
    """Devuelve (direccion_inicial, bytes) con todos los registros de datos del .ihx."""
    mem = {}
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln.startswith(':'): continue
        raw = bytes.fromhex(ln[1:])
        n, addr, typ = raw[0], (raw[1] << 8) | raw[2], raw[3]
        if (sum(raw) & 0xFF) != 0: raise ValueError("checksum HEX incorrecto: " + ln)
        if typ == 0:
            for i in range(n): mem[addr + i] = raw[4 + i]
        elif typ == 1: break
    if not mem: raise ValueError("el .ihx no contiene datos")
    lo, hi = min(mem), max(mem)
    return lo, bytes(mem.get(a, 0) for a in range(lo, hi + 1))

# ---------------------------------------------------------------- AMSDOS
def amsdos_header(name, load, length, entry, ftype=2):
    """Cabecera AMSDOS de 128 bytes (ftype 2 = binario)."""
    n, _, e = name.upper().partition('.')
    h = bytearray(128)
    h[0] = 0                                           # usuario 0
    h[1:9] = n[:8].ljust(8).encode('ascii'); h[9:12] = e[:3].ljust(3).encode('ascii')
    h[0x12] = ftype
    h[0x13:0x15] = struct.pack('<H', length & 0xFFFF)  # longitud de datos
    h[0x15:0x17] = struct.pack('<H', load)             # direccion de carga
    h[0x17] = 0                                        # primer bloque
    h[0x18:0x1A] = struct.pack('<H', length & 0xFFFF)  # longitud logica
    h[0x1A:0x1C] = struct.pack('<H', entry)            # direccion de ejecucion
    h[0x40:0x43] = struct.pack('<I', length)[:3]       # longitud real (24 bits)
    h[0x43:0x45] = struct.pack('<H', sum(h[0:0x43]) & 0xFFFF)   # suma de comprobacion de los bytes 0..66
    return bytes(h)

def amsdos_file(name, data, load, entry):
    return amsdos_header(name, load, len(data), entry) + data

# ---------------------------------------------------------------- DSK
TRACKS, SPT, SSZ, BLK = 40, 9, 512, 1024
DIR_ENTRIES = 64

def make_dsk(files, creator=b"cpcpack.py"):
    """files: lista de (nombre 'NOMBRE.EXT', contenido bytes, incluida ya la cabecera AMSDOS si procede)."""
    nblocks = TRACKS * SPT * SSZ // BLK            # 180
    disk = bytearray(b'\xE5' * (TRACKS * SPT * SSZ))   # sectores logicos en orden: pista*9 + sector
    nxt = DIR_ENTRIES * 32 // BLK                  # primer bloque libre (0 y 1 son el directorio)
    entries = []
    for fname, data in files:
        n, _, e = fname.upper().partition('.')
        data = data + b'\x00' * ((-len(data)) % 128)
        nb = max(1, -(-len(data) // BLK))
        blocks = list(range(nxt, nxt + nb)); nxt += nb
        if nxt > nblocks: raise ValueError("el disco esta lleno")
        for i, b in enumerate(blocks):
            chunk = data[i * BLK:(i + 1) * BLK]
            disk[b * BLK:b * BLK + len(chunk)] = chunk
        for ext in range(-(-nb // 16)):
            mine = blocks[ext * 16:(ext + 1) * 16]
            recs = min(128, (len(data) - ext * 16 * BLK + 127) // 128)
            ent = bytearray(32)
            ent[0] = 0; ent[1:9] = n[:8].ljust(8).encode('ascii'); ent[9:12] = e[:3].ljust(3).encode('ascii')
            ent[12] = ext & 31; ent[14] = ext >> 5; ent[15] = recs
            ent[16:16 + len(mine)] = bytes(mine)
            entries.append(bytes(ent))
    if len(entries) > DIR_ENTRIES: raise ValueError("directorio lleno")
    for i, ent in enumerate(entries): disk[i * 32:i * 32 + 32] = ent
    tsize = 256 + SPT * SSZ
    out = bytearray()
    hdr = bytearray(256)
    hdr[0:34] = b"MV - CPCEMU Disk-File\r\nDisk-Info\r\n"
    hdr[34:34 + len(creator[:14])] = creator[:14]
    hdr[48] = TRACKS; hdr[49] = 1; hdr[50:52] = struct.pack('<H', tsize)
    out += hdr
    for t in range(TRACKS):
        ti = bytearray(256)
        ti[0:12] = b"Track-Info\r\n"; ti[16] = t; ti[17] = 0; ti[20] = 2; ti[21] = SPT; ti[22] = 0x4E; ti[23] = 0xE5
        for s in range(SPT):
            ti[24 + s * 8:32 + s * 8] = bytes([t, 0, 0xC1 + s, 2, 0, 0, 0, 0])
        out += ti
        out += disk[t * SPT * SSZ:(t + 1) * SPT * SSZ]
    return bytes(out)

# ---------------------------------------------------------------- lector (para verificar)
def read_dsk(img):
    """Lee un DSK como lo haria AMSDOS y devuelve {nombre: contenido}."""
    assert img[:8] == b"MV - CPC", "cabecera DSK"
    tracks, sides, tsize = img[48], img[49], struct.unpack('<H', img[50:52])[0]
    assert sides == 1 and tsize == 256 + SPT * SSZ
    def sector(t, rid):
        base = 256 + t * tsize
        assert img[base:base + 10] == b"Track-Info"
        for s in range(img[base + 21]):
            e = base + 24 + s * 8
            if img[e + 2] == rid:
                off = base + 256 + s * SSZ
                return img[off:off + SSZ]
        raise KeyError((t, hex(rid)))
    def block(b):
        out = b''
        for k in (0, 1):
            ls = b * 2 + k; out += sector(ls // SPT, 0xC1 + ls % SPT)
        return out
    dirdata = block(0) + block(1)
    files = {}
    for i in range(DIR_ENTRIES):
        e = dirdata[i * 32:i * 32 + 32]
        if e[0] == 0xE5: continue
        name = e[1:9].decode('ascii').rstrip() + '.' + e[9:12].decode('ascii').rstrip()
        content = b''.join(block(b) for b in e[16:32] if b)
        recs = e[15]
        files.setdefault(name, []).append((e[12], content[:recs * 128]))
    return {n: b''.join(c for _, c in sorted(v)) for n, v in files.items()}

def parse_amsdos(data):
    h = data[:128]
    assert (sum(h[0:0x43]) & 0xFFFF) == struct.unpack('<H', h[0x43:0x45])[0], "checksum de cabecera AMSDOS"
    return dict(type=h[0x12], length=struct.unpack('<H', h[0x13:0x15])[0], load=struct.unpack('<H', h[0x15:0x17])[0],
                entry=struct.unpack('<H', h[0x1A:0x1C])[0], real=struct.unpack('<I', h[0x40:0x43] + b'\0')[0])
