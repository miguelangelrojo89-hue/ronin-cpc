# Niveles 3 y 4 + solucionador que replica las reglas del juego
from collections import deque
W,H=28,15
def blank(): return [[' ']*W for _ in range(H)]
def floor(g,row,gaps=()):
    for x in range(W): g[row][x]='#'
    for a,b in gaps:
        for x in range(a,b+1): g[row][x]=' '
def ladder(g,col,top,bot):
    for y in range(top,bot+1): g[y][col]='H'
def wall(g,col,rows):
    for y in rows: g[y][col]='='
def rope(g,row,c0,c1):
    for x in range(c0,c1+1): g[row][x]='-'
def put(g,x,y,ch): g[y][x]=ch
def rows(g): return [''.join(r).rstrip() for r in g]
def finish(g):
    assert g[1][25]==' ' and g[0][25]==' ',(g[1][25],g[0][25])
    put(g,25,0,'a'); put(g,26,0,'b'); put(g,27,0,'c'); put(g,25,1,'p'); put(g,27,1,'D')

def island(g,S,x0,x1):
    for x in range(x0,x1+1): g[S+1][x]='#'

def level5():
    g=blank(); floor(g,14)
    island(g,10,3,7); island(g,7,1,6); island(g,10,14,19); island(g,4,10,19); island(g,7,21,27); island(g,1,21,27)
    ladder(g,8,10,13); ladder(g,5,7,10); ladder(g,13,10,13); ladder(g,16,4,10); ladder(g,19,4,10); ladder(g,20,7,10); ladder(g,24,1,7)
    wall(g,12,(11,12,13)); wall(g,17,(9,10))
    rope(g,9,7,14)
    put(g,2,13,'P')
    for x,y in ((6,13),(16,13),(23,13),(4,10),(2,7),(15,10),(18,10),(12,4),(23,7),(26,7),(22,1)): put(g,x,y,'$')
    for x,y,c in ((20,13,'F'),(22,7,'E'),(12,4,'E'),(26,1,'F')): put(g,x,y,c)
    finish(g); return g

def level6():
    g=blank()
    island(g,13,0,6); island(g,13,21,27)
    island(g,10,8,12); island(g,10,18,22); island(g,7,3,8); island(g,7,14,19); island(g,1,12,27)
    ladder(g,7,10,13); ladder(g,9,7,10); ladder(g,17,1,7); ladder(g,23,10,13); ladder(g,26,1,13)
    wall(g,22,(0,1)); wall(g,11,(10,))
    rope(g,9,10,18); rope(g,6,8,14)
    put(g,2,13,'P')
    for x,y in ((5,13),(9,10),(4,7),(15,7),(14,1),(19,1),(20,10),(22,13),(24,1)): put(g,x,y,'$')
    for x,y,c in ((25,13,'F'),(19,10,'E'),(18,7,'F'),(16,1,'E')): put(g,x,y,c)
    finish(g); return g

def hill(g,c,S,hs):
    for i,h in enumerate(hs):
        for k in range(h): g[S-k][c+i]='r'
def gap(g,row,x0,x1):
    for x in range(x0,x1+1): g[row][x]=' '
def zig(g,c1,c2,c3,c4):
    """cinco plantas completas unidas por escalones de roca en los bordes (derecha, izquierda, derecha, izquierda).
    Cada escalera sube a una repisa; hay que saltar la apertura de 2 casillas para llegar al resto de la planta."""
    for r in (14,11,8,5,2): floor(g,r)
    for c,S in ((c1,13),(c3,7)):            # escalera en el borde derecho
        U=S-2
        g[U][c]=' '; g[U][c+1]=' '; g[U][c+2]='r'
        put(g,c,S,'r'); put(g,c+1,S-1,'r')
    for c,S in ((c2,10),(c4,4)):            # escalera en el borde izquierdo
        U=S-2
        g[U][c-1]=' '; g[U][c]=' '; g[U][c-2]='r'
        put(g,c,S,'r'); put(g,c-1,S-1,'r')
def hybrid(g,trans):
    """cinco plantas; cada paso de planta es un escalon de roca a la derecha ('R'), a la izquierda ('L') o una escalera ('H')"""
    for r in (14,11,8,5,2): floor(g,r)
    for (kind,c),S in zip(trans,(13,10,7,4)):
        U=S-2
        if kind=='R':
            g[U][c]=' '; g[U][c+1]=' '; g[U][c+2]='r'; put(g,c,S,'r'); put(g,c+1,S-1,'r')
        elif kind=='L':
            g[U][c-1]=' '; g[U][c]=' '; g[U][c-2]='r'; put(g,c,S,'r'); put(g,c-1,S-1,'r')
        else:
            ladder(g,c,S-3,S)

MOVED=[]
def place(g,golds,enemies):
    for x,y in golds:
        assert g[y][x]==' ',("oro",x,y,g[y][x]); g[y][x]='$'
    for x,y,c in enemies:
        def ok(xx): return 0<=xx<28 and g[y][xx]==' ' and g[y+1][xx] in '#=r'
        if not ok(x):
            cand=sorted((xx for xx in range(28) if ok(xx)),key=lambda xx:(abs(xx-x),xx))
            assert cand,("enemigo sin sitio",x,y)
            MOVED.append((x,y,cand[0])); x=cand[0]
        g[y][x]=c

def spikes(g,x0,x1,row):
    for x in range(x0,x1+1): g[row][x]='^'

def level7():
    g=blank()
    floor(g,14); floor(g,11,[(12,17)]); floor(g,8,[(12,17)])
    island(g,4,0,5); island(g,4,11,18); island(g,4,24,27); island(g,1,12,27)
    ladder(g,3,10,13); ladder(g,9,7,10); ladder(g,4,4,7)
    ladder(g,18,4,7); ladder(g,20,7,10); ladder(g,25,7,10); ladder(g,26,4,7); ladder(g,24,1,4)
    wall(g,22,(6,7))
    rope(g,3,5,11)
    spikes(g,12,17,13)
    put(g,2,13,'P')
    for x,y in ((5,10),(6,7),(2,4),(14,4),(16,4),(19,7),(22,10),(27,10),(24,7),(25,4),(16,1),(21,1)): put(g,x,y,'$')
    for x,y,c in ((7,7,'E'),(24,10,'F'),(15,4,'E'),(18,1,'F')): put(g,x,y,c)
    finish(g); return g

def level8():
    g=blank()
    floor(g,14); floor(g,11,[(8,12)])
    island(g,7,0,7); island(g,7,13,18); island(g,4,0,18); island(g,4,24,27); island(g,1,12,27)
    ladder(g,5,10,13); ladder(g,2,7,10); ladder(g,3,4,7); ladder(g,6,4,7); ladder(g,16,4,7); ladder(g,26,1,4)
    wall(g,5,(6,7)); wall(g,12,(3,4))
    rope(g,6,7,13); rope(g,3,18,24)
    spikes(g,8,12,13); spikes(g,19,23,10)
    put(g,2,13,'P')
    for x,y in ((1,10),(7,10),(1,7),(4,4),(9,4),(15,7),(14,4),(24,4),(14,1),(19,1)): put(g,x,y,'$')
    for x,y,c in ((16,13,'E'),(11,4,'F'),(14,7,'E'),(21,1,'F')): put(g,x,y,c)
    finish(g); return g

def level9():
    g=blank(); zig(g,24,3,24,3)
    hill(g,10,13,[1,1,1,1]); hill(g,12,10,[1,1,1])
    gap(g,8,11,16); rope(g,6,10,17)
    put(g,12,4,'='); rope(g,3,11,13)
    gap(g,2,13,18); rope(g,0,12,19)
    put(g,2,13,'P')
    place(g,[(5,13),(11,12),(18,13),(13,9),(8,10),(20,10),(7,7),(21,7),(6,4),(18,4),(9,1),(22,1)],
            [(19,13,'F'),(17,10,'E'),(22,7,'F'),(15,4,'E'),(8,1,'F')])
    finish(g); return g

def level10():
    g=blank(); zig(g,22,5,22,5)
    spikes(g,9,13,13); rope(g,12,8,14)
    spikes(g,12,17,10); rope(g,9,11,18); gap(g,8,12,17); rope(g,6,11,18)
    hill(g,10,4,[1,1,1])
    put(g,16,4,'='); rope(g,3,15,17)
    gap(g,2,12,18); rope(g,0,11,19)
    put(g,2,13,'P')
    place(g,[(4,13),(16,13),(8,10),(20,10),(9,7),(20,7),(11,3),(19,4),(8,1),(21,1),(24,1)],
            [(18,13,'F'),(7,10,'E'),(19,7,'F'),(14,4,'E'),(22,1,'E')])
    finish(g); return g

def level11():
    g=blank(); zig(g,24,3,24,3)
    gap(g,11,9,15); gap(g,8,9,15); spikes(g,9,15,13)
    rope(g,12,8,16); rope(g,9,8,16); rope(g,6,8,16)
    hill(g,12,4,[1,1,1])
    put(g,18,1,'='); rope(g,0,17,19)
    put(g,2,13,'P')
    place(g,[(5,13),(19,13),(6,10),(19,10),(6,7),(20,7),(22,7),(5,4),(19,4),(10,1),(14,1),(23,1)],
            [(20,13,'E'),(18,10,'F'),(18,7,'F'),(15,4,'E'),(21,1,'E')])
    finish(g); return g

def level12():
    """Noche: triple altura de pozo (planta 4 -> pinchos en la 2) y tres cuerdas apiladas"""
    g=blank(); zig(g,22,5,22,5)
    spikes(g,9,15,13); rope(g,12,8,16); hill(g,16,13,[1,1])
    gap(g,5,12,17); gap(g,8,12,17); spikes(g,12,17,10)
    rope(g,9,11,18); rope(g,6,11,18); rope(g,3,11,18)
    put(g,15,1,'='); rope(g,0,14,16); hill(g,9,1,[1])
    put(g,2,13,'P')
    place(g,[(5,13),(20,13),(8,10),(20,10),(8,7),(20,7),(8,4),(19,4),(8,1),(11,1),(22,1)],
            [(19,13,'F'),(7,10,'E'),(19,7,'F'),(14,4,'E'),(18,1,'F')])
    finish(g); return g

def level13():
    """Castillo: cadenas de cuerdas, columnas bajas y huecos largos en las cinco plantas"""
    g=blank(); zig(g,23,4,23,4)
    spikes(g,9,13,13); rope(g,12,8,14); hill(g,16,13,[1,1,1])
    gap(g,11,8,12); gap(g,11,15,19); rope(g,9,7,13); rope(g,9,14,20)
    gap(g,8,10,16); rope(g,6,9,17); put(g,19,7,'='); rope(g,6,18,20)
    gap(g,5,12,17); rope(g,3,11,18)
    gap(g,2,13,19); rope(g,0,12,20); put(g,23,1,'='); rope(g,0,22,24)
    put(g,2,13,'P')
    place(g,[(5,13),(15,13),(6,10),(13,10),(21,10),(7,7),(21,7),(6,4),(21,4),(8,1),(11,1),(21,1)],
            [(20,13,'F'),(14,10,'E'),(22,7,'F'),(8,4,'E'),(17,1,'E')])
    finish(g); return g

def level14():
    """Pozo total: un solo pozo atraviesa tres plantas hasta los pinchos del suelo; cuatro cuerdas apiladas"""
    g=blank(); zig(g,23,4,23,4)
    for r in (11,8,5): gap(g,r,11,16)
    spikes(g,11,16,13)
    rope(g,12,10,17); rope(g,9,10,20); rope(g,6,10,17); rope(g,3,10,17)
    put(g,19,10,'='); hill(g,17,7,[1,1,1]); hill(g,7,4,[1,1]); hill(g,19,13,[1,1,1])
    gap(g,2,12,18); rope(g,0,11,19); put(g,22,1,'='); rope(g,0,21,23)
    put(g,2,13,'P')
    place(g,[(5,13),(9,13),(21,10),(7,10),(8,7),(20,7),(6,4),(20,4),(8,1),(21,1),(24,1)],
            [(17,13,'F'),(15,10,'E'),(21,7,'F'),(14,4,'E'),(10,1,'F')])
    finish(g); return g

def level15():
    """Islas: cuerdas encadenadas sobre pinchos, con islotes de dos casillas entre cuerda y cuerda"""
    g=blank(); zig(g,22,6,22,6)
    spikes(g,12,16,13); rope(g,12,11,17)
    gap(g,8,9,13); gap(g,8,16,20); spikes(g,9,13,10); spikes(g,16,20,10)
    rope(g,9,8,14); rope(g,9,15,21)
    rope(g,6,8,14); rope(g,6,15,21)
    gap(g,5,11,17); put(g,20,4,'='); rope(g,3,10,21)
    gap(g,2,12,18); rope(g,0,11,19); hill(g,23,1,[1])
    put(g,2,13,'P')
    place(g,[(5,13),(8,13),(19,13),(8,10),(14,10),(21,10),(8,7),(14,7),(7,4),(19,4),(8,1),(22,1)],
            [(18,13,'F'),(7,10,'E'),(17,7,'F'),(8,4,'E'),(10,1,'F'),(24,1,'E')])
    finish(g); return g

def level16():
    """Final: todas las ideas juntas, seis guardianes"""
    g=blank(); zig(g,24,3,24,3)
    spikes(g,8,12,13); rope(g,12,7,13); hill(g,16,13,[1,1])
    gap(g,11,8,12); gap(g,11,15,19); rope(g,9,7,13); rope(g,9,14,22); put(g,21,10,'=')
    gap(g,8,10,15); spikes(g,13,14,10); rope(g,6,9,16); hill(g,18,7,[1,1,1])
    gap(g,5,11,17); rope(g,3,10,18); put(g,20,4,'='); rope(g,3,19,21)
    gap(g,2,13,19); rope(g,0,12,20); put(g,23,1,'='); rope(g,0,22,24)
    put(g,2,13,'P')
    place(g,[(5,13),(14,13),(19,13),(6,10),(22,10),(23,10),(6,7),(21,7),(6,4),(8,4),(21,4),(8,1),(11,1),(21,1)],
            [(20,13,'F'),(17,10,'E'),(22,7,'F'),(12,4,'E'),(16,4,'F'),(15,1,'E')])
    finish(g); return g

def level17():
    """Desierto rojo: roca, escalera, roca, escalera"""
    g=blank(); hybrid(g,[('R',24),('H',12),('L',3),('H',22)])
    spikes(g,8,12,13); rope(g,12,7,13); hill(g,16,13,[1,1])
    gap(g,11,15,19); rope(g,9,14,20)
    put(g,8,7,'='); rope(g,6,7,9)
    gap(g,5,10,16); rope(g,3,9,17)
    put(g,24,1,'='); rope(g,0,23,24)
    put(g,2,13,'P')
    place(g,[(4,13),(18,13),(22,10),(13,10),(15,7),(6,7),(7,4),(19,4),(10,1),(18,1)],
            [(20,13,'F'),(17,10,'E'),(14,7,'F'),(20,4,'E'),(13,1,'F')])
    finish(g); return g

def level18():
    """Cian invertido: se empieza por la derecha y los escalones alternan izquierda, derecha, izquierda, derecha"""
    g=blank(); hybrid(g,[('L',3),('R',24),('L',3),('R',24)])
    spikes(g,14,19,13); rope(g,12,13,20); hill(g,8,13,[1,1,1])
    gap(g,11,14,19); spikes(g,14,19,13); rope(g,9,13,20)
    gap(g,8,9,15); rope(g,6,8,16); put(g,19,7,'='); rope(g,6,18,20)
    gap(g,5,10,16); rope(g,3,9,17); hill(g,19,4,[1,1])
    put(g,26,13,'P')
    place(g,[(25,13),(6,13),(6,10),(21,10),(6,7),(22,7),(6,4),(21,4),(8,1),(12,1),(22,1)],
            [(22,13,'F'),(10,10,'E'),(11,7,'E'),(14,4,'F'),(16,1,'E')])
    finish(g); return g

def level19():
    """Violeta: escaleras y rocas con una cadena de dos cuerdas y un islote en la planta 3"""
    g=blank(); hybrid(g,[('H',18),('R',24),('H',8),('L',3)])
    spikes(g,9,13,13); rope(g,12,8,14); hill(g,21,13,[1,1])
    gap(g,11,19,22); rope(g,9,17,23)
    gap(g,8,10,14); gap(g,8,17,21); rope(g,6,16,22); rope(g,6,9,15)
    put(g,6,4,'='); hill(g,12,4,[1,1,1]); rope(g,3,5,7)
    gap(g,2,12,18); rope(g,0,11,19); hill(g,22,1,[1])
    put(g,2,13,'P')
    place(g,[(4,13),(16,13),(14,10),(7,10),(23,7),(6,7),(15,4),(20,4),(8,1),(21,1),(10,1)],
            [(19,13,'F'),(16,10,'E'),(18,7,'E'),(10,4,'F'),(15,1,'E')])
    finish(g); return g

def level3():
    g=blank()
    for r,gp in ((14,()),(11,()),(8,[(9,16)]),(5,()),(2,())): floor(g,r,gp)
    for c in (6,21,25): ladder(g,c,10,13)          # F1 -> F2
    ladder(g,27,7,10)                               # F2 -> F3
    ladder(g,3,4,7)                                 # F3 -> F4
    for c in (8,16,23): ladder(g,c,1,4)             # F4 <-> F5
    wall(g,14,(12,13)); wall(g,23,(9,10)); wall(g,12,(3,4)); wall(g,20,(0,1))
    rope(g,6,8,17)
    put(g,2,13,'P')
    for x,y in ((10,13),(17,13),(23,13),(9,10),(24,10),(6,7),(20,7),(5,4),(19,4),(26,4),(12,1),(22,1)): put(g,x,y,'$')
    for x,y,c in ((18,13,'F'),(15,10,'E'),(22,7,'F'),(20,4,'E'),(11,1,'E')): put(g,x,y,c)
    finish(g); return g

def level4():
    g=blank()
    for r,gp in ((14,[(10,17)]),(11,()),(8,()),(5,[(11,18)]),(2,())): floor(g,r,gp)
    ladder(g,22,10,13)                              # F1 -> F2
    ladder(g,16,7,10); ladder(g,9,7,10); ladder(g,2,7,10)   # F2 <-> F3
    ladder(g,4,4,7)                                 # F3 -> F4
    ladder(g,24,1,4)                                # F4 -> F5
    wall(g,12,(9,10)); wall(g,6,(6,7))
    rope(g,12,9,18); rope(g,3,10,19)
    put(g,2,13,'P')
    for x,y in ((6,13),(20,13),(25,13),(18,10),(25,10),(5,10),(12,7),(21,7),(5,7),(7,4),(22,4),(8,1),(12,1),(20,1)): put(g,x,y,'$')
    for x,y,c in ((24,13,'F'),(20,10,'E'),(23,7,'F'),(26,4,'E'),(17,1,'F')): put(g,x,y,c)
    finish(g); return g

# ---------- solucionador (mismas reglas que game.c) ----------
def solve(rowsl,use_rope=True,verbose=False):
    global LAST_TRAPS
    g=[list(r.ljust(W)) for r in rowsl]
    if not use_rope:
        for y in range(H):
            for x in range(W):
                if g[y][x]=='-': g[y][x]=' '
    def cell(x,y): return '=' if x<0 or x>=W or y<0 or y>=H else g[y][x]
    def solid(x,y): return x<0 or x>=W or y<0 or y>=H or g[y][x] in '#=r'
    def sup(x,y): return cell(x,y) in 'H-' or solid(x,y+1) or cell(x,y+1)=='H'
    start=None; golds=[]; door=None
    for y in range(H):
        for x in range(W):
            c=g[y][x]
            if c=='P': start=(x,y); g[y][x]=' '
            elif c=='$': golds.append((x,y))
            elif c=='D': door=(x,y)
    def succ(x,y):
        if not sup(x,y): return [(x,y+1)]
        nxt=[]
        for dx in (-1,1):
            if not solid(x+dx,y): nxt.append((x+dx,y))
        if cell(x,y)=='H' and cell(x,y-1)=='H': nxt.append((x,y-1))
        if not solid(x,y+1): nxt.append((x,y+1))
        if cell(x,y)!='H' and solid(x,y+1):
            if cell(x,y-1)=='-': nxt.append((x,y-1))
            for dx in (-1,1):            # encaramarse a una roca
                if cell(x+dx,y)=='r' and not solid(x,y-1) and not solid(x+dx,y-1): nxt.append((x+dx,y-1))
            for dx in (-1,1):            # salto en horizontal
                for k in range(1,5):
                    if solid(x+dx*k,y): break
                    nxt.append((x+dx*k,y))
        return nxt
    def ok_state(n): return not (n[1]>=H-1 or cell(n[0],n[1])=='^')
    prev={start:None}; dist={start:0}; q=deque([start])
    while q:
        s=q.popleft()
        for n in succ(*s):
            if ok_state(n) and n not in prev: prev[n]=s; dist[n]=dist[s]+1; q.append(n)
    globals()['LAST_DIST']=dist
    reach=set(prev); globals()["LAST_REACH"]=reach
    miss=[p for p in golds if p not in reach]
    okk=door in reach and not miss
    rev={}
    for a in reach:
        for b in succ(*a):
            if b in reach: rev.setdefault(b,[]).append(a)
    good=set(); dd={}
    if door in reach:
        good={door}; dd={door:0}; dq=deque([door])
        while dq:
            c=dq.popleft()
            for a in rev.get(c,[]):
                if a not in good: good.add(a); dd[a]=dd[c]+1; dq.append(a)
    globals()['LAST_DD']=dd
    LAST_TRAPS=sorted(st for st in reach-good if sup(*st))
    path=[]; s=door
    while okk and s is not None: path.append(s); s=prev[s]
    return okk,golds,miss,door in reach,path[::-1]

def add_key(rowsl):
    """la llave va en la casilla de suelo (alcanzable y desde la que se llega a la puerta) que obliga a mayor desvio"""
    rr=[r.ljust(W) for r in rowsl]
    ok,golds,miss,door_ok,path=solve(rr)
    assert door_ok and not miss,"nivel no completable"
    d=LAST_DIST; dd=LAST_DD; dstart=len(path)-1
    def free(x,y): return rr[y][x]==' ' and y+1<H and rr[y+1][x] in '#=r'
    ps=set(path)
    def away(p): return min(abs(p[0]-q[0])+abs(p[1]-q[1]) for q in ps)
    cands=[p for p in d if p in dd and free(*p) and abs(p[0]-27)+abs(p[1]-1)>4 and away(p)>=3]
    if not cands: cands=[p for p in d if p in dd and free(*p) and abs(p[0]-27)+abs(p[1]-1)>4]
    best=max(cands,key=lambda p:(d[p]+dd[p]-dstart,d[p]))
    x,y=best; rr[y]=rr[y][:x]+'k'+rr[y][x+1:]
    return [r.rstrip() for r in rr],best,d[best]+dd[best]-dstart

def describe(path):
    ds=0; us=0; ropes=0
    for a,b in zip(path,path[1:]):
        if b[1]>a[1] and b[0]==a[0]: ds+=1
        if b[1]<a[1] and b[0]==a[0]: us+=1
    return ds,us

if __name__=="__main__":
    for n,f in (("3",level3),("4",level4),("5",level5),("6",level6),("7",level7),("8",level8),("9",level9),("10",level10),("11",level11),("12",level12),("13",level13),("14",level14),("15",level15),("16",level16),("17",level17),("18",level18),("19",level19)):
        MOVED.clear(); r=rows(f()); print("--- nivel",n, ("| enemigos recolocados: %s"%MOVED) if MOVED else "")
        for y,l in enumerate(r): print("%2d |%s|"%(y,l.ljust(28)))
        ok,golds,miss,door_ok,path=solve(r)
        traps=list(LAST_TRAPS)
        print("completable:",ok,"| oro:",len(golds),"| sin alcanzar:",miss,"| puerta alcanzable:",door_ok)
        ok2=solve(r,use_rope=False)[0]
        print("sin cuerdas se puede completar:",ok2,"(debe ser False)")
        print("posiciones atascadas sin salida:",len(traps),traps[:8])
        print("pasos bajando/subiendo en el camino mas corto a la puerta:",describe(path),"longitud",len(path))
