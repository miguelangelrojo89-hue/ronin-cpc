# Sprites, fuente y niveles base (extraidos del gen.py del port de QL)
# Genera data.h: nivel, sprites y fuente a partir de las mismas definiciones del prototipo web
def rep(s,n): return s*n
LEVEL=[
"",
"H"+" "*3+"E"+" "*3+"$"+" "*5+"$"+" "*5+"$"+" "*6+"D",
"H"+"#"*27,
"H",
"H"+" "*5+"$"+" "*7+"E"+" "*5+"$"+" "*6+"H",
"#"*27+"H",
" "*27+"H",
"H"+" "*7+"$"+" "*3+"E"+" "*9+"$"+" "*4+"H",
"H"+"#"*27,
"H",
"H"+" "*5+"$"+" "*9+"E"+" "*3+"$"+" "*6+"H",
"#"*27+"H",
" "*27+"H",
"  P"+" "*5+"$"+" "*9+"$"+" "*3+"E"+" "*4+"H",
"#"*28]
assert all(len(r)<=28 for r in LEVEL) and len(LEVEL)==15

LEVEL2=[
"",
"H"+" "*5+"$"+" "*5+"$"+" "*8+"$"+" "*2+"F"+" "*2+"D",
"H"+"#"*14+"  "+"#"*11,
"H",
"H"+" "*3+"E"+" "*1+"$"+" "*9+"$"+" "*5+"$"+" "*4+"H",
"#"*11+"  "+"#"*14+"H",
" "*27+"H",
"H"+" "*7+"$"+" "*5+"$"+" "*7+"F"+" "*4+"H",
"H"+"#"*16+"  "+"#"*9,
"H",
"H"+" "*3+"$"+" "*10+"E"+" "*6+"$"+" "*4+"H",
"#"*9+"  "+"#"*16+"H",
" "*27+"H",
"  P"+" "*3+"$"+" "*11+"$"+" "*2+"F"+" "*2+"$"+" "*2+"H",
"#"*13+"  "+"#"*13,
]
assert len(LEVEL2)==15 and all(len(r)<=28 for r in LEVEL2)
assert LEVEL2[1].ljust(28)[27]=='D' and LEVEL2[13].ljust(28)[27]=='H'
helm=["...XX...","..XXXX..","XXXXXXXX","..WKKW.."]
body=["..WBBW..",".WBBBBW.","..WBBW..","..WBBW..",".WWWWWW."]
S={}
S['idle']=helm+body+["..WWWW..","..R..R..",".RR..RR."]
S['walk']=helm+body+[".WW..WW.",".R....R.","RR....RR"]
S['climbA']=["...XX...","..XXXX..","XXXXXXXX","..WWWW..","W.WWWW..","W.WWWW..","..WWWW..","..WWWW..",".WWWWWW.","..WWWW..","..R..R..",".RR..RR."]
S['climbB']=["...XX...","..XXXX..","XXXXXXXX","..WWWW..","..WWWW.W","..WWWW.W","..WWWW..","..WWWW..",".WWWWWW.","..WWWW..","..R..R..",".RR..RR."]
S['prone']=["........"]*8+["......XX","WWWBBWWK","RRWWWWW.","........"]
coin=["........"]*2+["..YYYY..",".YYYYYY.","YYYYYYYY","YYYYYYYY","YYYYYYYY","YYYYYYYY",".YYYYYY.","..YYYY.."]+["........"]*2
for (x,y) in ((3,3),(4,3),(5,3),(2,4),(3,4),(3,5),(4,5),(4,6),(5,6),(2,7),(3,7),(4,7),(3,2),(4,8)):
    coin[y]=coin[y][:x]+'K'+coin[y][x+1:]
S['gold']=coin
S['key']=["........","..WWW...",".W...W..",".W...W..","..WWW...","...W....","...W....","...WW...","...W....","...WW...","........","........"]
g=lambda f:[''.join(f(x,y) for x in range(8)) for y in range(12)]
S['brick']=g(lambda x,y:'K' if (y%6==5 or x==(3 if y<6 else 7)) else 'R')
S['ladder']=g(lambda x,y:'G' if (x==1 or x==6 or y%3==1) else '.')
S['rope']=g(lambda x,y:'C' if y==4 else '.')
# puerta estrecha (6 px) + poste del cartel a la derecha (2 px)
S['doorC']=['YYYYYYWW']+['YBBBBYWW']*4+['YBBYBYWW']+['YBBBBYWW']*5+['YYYYYYWW']
S['doorO']=['YYYYYYWW']+['YGGGGYWW']*10+['YYYYYYWW']
# cartel EXIT: 24x12, fondo verde, borde blanco, letras blancas, dos postes; se corta en 3 baldosas
FONT0={'E':"111100110100111",'X':"101101010101101",'I':"111010010010111",'T':"111010010010010"}
board=[['.']*24 for _ in range(12)]
for x in range(24): board[1][x]='W'; board[9][x]='W'
for y in range(2,9):
    for x in range(24): board[y][x]='G'
    board[y][0]='W'; board[y][23]='W'
for y in (10,11):
    for x in (0,1,22,23): board[y][x]='W'
for off,ch in ((4,'E'),(8,'X'),(12,'I'),(16,'T')):
    for r in range(5):
        for c in range(3):
            if FONT0[ch][r*3+c]=='1': board[3+r][off+c]='W'
for k,n in enumerate(('signA','signB','signC')): S[n]=[''.join(board[y][k*8:k*8+8]) for y in range(12)]
S['spike']=g(lambda x,y:('W' if y<8 else 'C') if (y>=6 and min(abs(x-1),abs(x-5))<=(y-6)//2) else '.')
S['rock']=['WWWWWWWW','WWWWWWWC','WWKWWWWC','WWWKWWCC','WWWWWWCC','WKWWWWCC','WWWWWCCC','WWWWWWCC','WWKWWWCC','WWWWCCCC','WCCCCCCC','CCCCCCCC']
S['post']=['WW......']*12
# columnas de marmol: capitel arriba, base abajo, fuste simple
shaft='..WWWC..'; cap=['WWWWWWWW','WWWWWWWC','.WWWWWC.']; base=['.WWWWWC.','WWWWWWWC','WWWWWWWW']
S['colTop']=cap+[shaft]*9
S['colMid']=[shaft]*12
S['colBot']=[shaft]*9+base
S['colOne']=cap+[shaft]*6+base
order=['idle','walk','climbA','climbB','prone','gold','brick','ladder','rope','doorC','doorO','signA','signB','signC','post','colOne','colTop','colMid','colBot','spike','rock','key']
for k in order: assert len(S[k])==12 and all(len(r)==8 for r in S[k]),k
FONT={'B':"110101110101110",'H':"101101111101101",'M':"101111111101101",'X':"101101010101101",'Y':"101101010010010",'Z':"111001010100111",'0':"111101101101111",'1':"010110010010111",'2':"111001111100111",'3':"111001111001111",'4':"101101111001001",'5':"111100111001111",'6':"111100111101111",'7':"111001001001001",'8':"111101111101111",'9':"111101111001111",'A':"010101111101101",'C':"011100100100011",'D':"110101101101110",'E':"111100110100111",'F':"111100110100100",'G':"011100101101011",'I':"111010010010111",'L':"100100100100111",'N':"110101101101101",'O':"010101101101010",'P':"110101110100100",'R':"110101110101101",'S':"011100010001110",'T':"111010010010010",'U':"101101101101111",'V':"101101101101010"}
assert all(len(v)==15 for v in FONT.values())
