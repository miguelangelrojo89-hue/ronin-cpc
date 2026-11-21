#!/usr/bin/env python3
"""Construye El Roningasa Ronin para Amstrad CPC.

    python3 build.py          -> genera ronin.dsk y RONIN.BIN (necesita SDCC >= 4.0 en el PATH)
    python3 build.py test     -> pruebas en el PC (gcc): logica, fuzzing con sanitizers y capturas de pantalla
    python3 build.py pack     -> prueba del empaquetado AMSDOS/DSK (solo Python)
"""
import os, re, subprocess, sys
import cpcpack

CODE_LOC, DATA_LOC = 0x4000, 0x9800     # codigo desde &4000 (22 KB de margen); variables (~3 KB) desde &9800, por debajo de HIMEM de BASIC (&A67B)

def run(cmd):
    print("  $", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.stdout.strip(): print(r.stdout.rstrip())
    if r.stderr.strip(): print(r.stderr.rstrip())
    if r.returncode: sys.exit("fallo al ejecutar " + cmd[0])

def build():
    for tool in ("sdcc", "sdasz80"):
        if subprocess.run(["which", tool], capture_output=True).returncode:
            sys.exit("No encuentro '%s'. Instala SDCC (https://sdcc.sourceforge.net)." % tool)
    run([sys.executable, "gen_cpc.py"])
    run(["sdasz80", "-plosgff", "crt0.s"])
    run(["sdcc", "-mz80", "--std-sdcc99", "--opt-code-size", "-c", "game.c"])
    run(["sdcc", "-mz80", "--no-std-crt0", "--code-loc", hex(CODE_LOC), "--data-loc", hex(DATA_LOC),
         "crt0.rel", "game.rel", "-o", "ronin.ihx"])
    lo, img = cpcpack.ihx_to_image(open("ronin.ihx").read())
    if lo != CODE_LOC: sys.exit("el codigo no empieza en %#x (empieza en %#x)" % (CODE_LOC, lo))
    end = lo + len(img)
    print("codigo+datos constantes: %d bytes (&%04X-&%04X); variables desde &%04X" % (len(img), lo, end - 1, DATA_LOC))
    if end > DATA_LOC: sys.exit("el codigo (&%04X) invade el area de variables (&%04X): sube DATA_LOC" % (end, DATA_LOC))
    entry = CODE_LOC
    if os.path.exists("ronin.map"):
        m = re.search(r"([0-9A-Fa-f]{8})\s+_start\b", open("ronin.map").read())
        if m: entry = int(m.group(1), 16)
    f = cpcpack.amsdos_file("RONIN.BIN", img, lo, entry)
    open("RONIN.BIN", "wb").write(f)
    open("ronin.dsk", "wb").write(cpcpack.make_dsk([("RONIN.BIN", f)]))
    back = cpcpack.read_dsk(open("ronin.dsk", "rb").read())["RONIN.BIN"]
    assert back == f + b"\0" * (len(back) - len(f)), "verificacion del .dsk"
    print("OK: RONIN.BIN (%d bytes con cabecera AMSDOS) y ronin.dsk. En el CPC:  RUN\"RONIN.BIN\"" % len(f))

def test():
    run(["gcc", "-std=c99", "-Wall", "-Wextra", "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=undefined",
         "-o", "test_host", "test_host.c"])
    r = subprocess.run(["./test_host"]); sys.exit(r.returncode)

if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "build"
    if a == "test": run([sys.executable, "gen_cpc.py"]); test()
    elif a == "pack": run([sys.executable, "test_pack.py"])
    else: build()
