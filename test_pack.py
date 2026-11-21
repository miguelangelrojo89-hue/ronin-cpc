"""Prueba del empaquetado: .ihx -> binario -> cabecera AMSDOS -> .dsk -> lectura independiente."""
import os, random, cpcpack as P
random.seed(7)
def mk_ihx(base, data):
    out=[]
    for i in range(0,len(data),16):
        ch=data[i:i+16]; rec=bytes([len(ch),((base+i)>>8)&255,(base+i)&255,0])+ch
        out.append(':'+(rec+bytes([(-sum(rec))&255])).hex().upper())
    out.append(':00000001FF'); return "\n".join(out)
for size in (500, 16384-128, 16384, 20000, 23000):
    code=bytes(random.randrange(256) for _ in range(size))
    lo,img=P.ihx_to_image(mk_ihx(0x4000,code))
    assert lo==0x4000 and img==code, "ihx"
    f=P.amsdos_file("RONIN.BIN",img,lo,0x4000)
    dsk=P.make_dsk([("RONIN.BIN",f),("LEEME.TXT",b"hola\r\n"*30)])
    assert len(dsk)==256+40*(256+9*512), len(dsk)
    back=P.read_dsk(dsk)
    assert sorted(back)==["LEEME.TXT","RONIN.BIN"], sorted(back)
    got=back["RONIN.BIN"]; info=P.parse_amsdos(got)
    assert info==dict(type=2,length=size&0xFFFF,load=0x4000,entry=0x4000,real=size), info
    assert got[128:128+size]==code and set(got[128+size:])<= {0}
    assert back["LEEME.TXT"].startswith(b"hola\r\n")
    print("ok  binario de %5d bytes: %d extents, cabecera AMSDOS y contenido verificados"%(size,-(-(size+128)//16384)))
# formato de cabecera: valores fijos conocidos
h=P.amsdos_header("RONIN.BIN",0x4000,1234,0x4000)
assert h[1:12]==b"RONIN   BIN" and h[0x12]==2 and h[0x15:0x17]==b"\x00\x40" and h[0x1A:0x1C]==b"\x00\x40"
print("ok  cabecera AMSDOS")
