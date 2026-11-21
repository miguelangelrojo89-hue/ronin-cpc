/* El Roningasa Ronin - port para Amstrad CPC 464/664/6128 (Z80, Mode 1: 320x200, 4 plumas).
   Compilar con SDCC (-mz80). Sin libc, sin multiplicaciones ni divisiones en el bucle de juego.
   Los sprites vienen prepaquetados en formato Mode 1 (con mascara) desde gen_cpc.py y el repintado
   es por celdas sucias, igual que en la version de QL.

   Toda la interaccion con el firmware pasa por fw()/fwcall() (trampolin en crt0.s), de modo que este
   mismo fichero se compila tambien en el PC (-DHOST) para las pruebas automaticas. */
typedef unsigned char u8; typedef signed char s8;
typedef unsigned short u16;
#include "data.h"

#define GW 28
#define GH 15
#define GX 2             /* byte de pantalla donde empieza la zona de juego (2 bytes por celda = 8 px) */
#define YOFF 13          /* linea de pantalla donde empieza la zona de juego (arriba va el titulo) */
#define HUDY 194         /* linea de los marcadores */
#define SIDEX 240        /* columna (pixel) de la barra lateral */
#define P_W 1            /* plumas: 0 negro, 1 blanco, 2 color del tema, 3 amarillo */
#define P_R 2
#define P_Y 3

/* ---------- capa de plataforma ---------- */
#ifdef HOST
static u8 vram[16384];
#define VRAM ((volatile u8*)vram)
#else
#define VRAM ((volatile u8*)0xC000)
#endif

u16 fw_addr, fw_af, fw_bc, fw_de, fw_hl;      /* registros de entrada/salida de fwcall() */
extern void fwcall(void);                     /* llama a la rutina de firmware fw_addr (crt0.s) */

#define KM_READ_CHAR   0xBB09
#define KM_TEST_KEY    0xBB1E
#define KM_ARM_BREAK   0xBB45
#define KM_DISARM_BREAK 0xBB48
#define SCR_RESET      0xBC02
#define SCR_SET_MODE   0xBC0E
#define SCR_SET_INK    0xBC32
#define SCR_SET_BORDER 0xBC38
#define MC_WAIT_FLYBACK 0xBD19

static void fw(u16 addr,u8 a,u8 b,u8 c){
  fw_addr=addr; fw_af=((u16)a)<<8; fw_bc=((u16)b<<8)|c; fw_de=0; fw_hl=0; fwcall();
}
static void setink(u8 pen,u8 ink){ fw(SCR_SET_INK,pen,ink,ink); }
static void sync(void){ fw(MC_WAIT_FLYBACK,0,0,0); }                 /* espera al barrido vertical (50 Hz) */
static u8 keydown(u8 k){ fw(KM_TEST_KEY,k,0,0); return !((u8)fw_af&0x40); }   /* NZ = pulsada */
static void flushkeys(void){ do fw(KM_READ_CHAR,0,0,0); while((u8)fw_af&1); }  /* vacia el buffer de teclado */

/* teclas del CPC (numero de tecla del firmware) -> mascara con el mismo formato que en la version de QL */
static u8 readkeys(void){
  u8 k=0;
  if(keydown(8)||keydown(74)) k|=2;            /* izquierda | joystick */
  if(keydown(0)||keydown(72)) k|=4;            /* arriba */
  if(keydown(1)||keydown(75)) k|=16;           /* derecha */
  if(keydown(2)||keydown(73)) k|=128;          /* abajo */
  if(keydown(47)||keydown(77)||keydown(76)) k|=64;   /* ESPACIO | disparo */
  if(keydown(66)) k|=8;                        /* ESC */
  if(keydown(6)||keydown(18)) k|=1;            /* ENTER | RETURN */
  return k;
}

/* ---------- datos ---------- */
static u8 g[GH][32];
static u8 rowof[GH*12];
static u8 dirty[GH][32]; static u16 ndirty; static u16 dlist[GW*GH];
static u16 lineoff[200];                        /* desplazamiento de cada linea en la memoria de video */
typedef struct{ short x,y,sx,sy; s8 face; u8 air,jl,prone,swing,moving; u8 a; } Pl;
typedef struct{ short x,y,sx,sy; s8 face,dir; u8 a,cd,dead,hat; } En;
typedef struct{ short xf,y; s8 d; u8 on; } Bu;
static Pl p; static En en[8]; static u8 nen;
static Bu pb[2],eb[4];
static u8 state,coins,haskey,hud_dirty,msg_dirty; static s8 digdir; static s8 lives; static u16 score,rs;
static const s8 JY[5]={0,-3,-7,-8,-5};
static const u8 THEMEINK[12]={6,2,18,8,20,15,11,7,19,16,21,14};   /* tinta de la pluma 2 en cada tema */
static short doorx,doory;
#ifndef STARTLVL
#define STARTLVL 0
#endif
#define NLEV 19
static u8 lvl, lvl_last;
static u8 theme;

static u8 cheat,cidx,cprev;               /* truco: teclear Q W E R T Y = vidas infinitas */
static const u8 CHEATKEY[6]={67,59,58,50,51,43};
static const char CHEATCH[7]="QWERTY";
static void cheat_feed(char ch){
  if(cheat) return;
  if(ch==CHEATCH[cidx]){ if(++cidx==6){ cheat=1; hud_dirty=1; } } else cidx=(ch=='Q')?1:0;
}
static void cheat_scan(void){
  u8 i,n=0,d;
  for(i=0;i<6;i++) if(keydown(CHEATKEY[i])) n|=(u8)(1<<i);
  d=n&~cprev; cprev=n;
  for(i=0;i<6;i++) if(d&(1<<i)) cheat_feed(CHEATCH[i]);
}
static u16 rnd(void){ rs^=rs<<7; rs^=rs>>9; rs^=rs<<8; return rs; }
static u8 cell(short x,short y){ if(x<0||x>=GW||y<0||y>=GH) return '='; return g[y][x]; }
static u8 solid(short x,short y){ u8 c; if(x<0||x>=GW||y<0||y>=GH) return 1; c=g[y][x]; return c=='#'||c=='='||c=='r'; }
static u8 supported(short x,short y){ u8 c=cell(x,y); return c=='H'||c=='-'||solid(x,y+1)||cell(x,y+1)=='H'; }
static void markcell(short x,short y){ if(!dirty[y][x]){ dirty[y][x]=1; dlist[ndirty++]=(y<<5)|x; } }
static void markall(void){ short x,y; ndirty=0; for(y=0;y<GH;y++) for(x=0;x<GW;x++){ dirty[y][x]=1; dlist[ndirty++]=(y<<5)|x; } }

static u16 o24(u8 n){ return ((u16)n<<4)+((u16)n<<3); }   /* n*24 sin multiplicar */

/* indices en TILES (17 baldosas de 24 bytes): 0 oro,1 ladrillo,2 escalera,3 cuerda,4/5 puerta cerrada/abierta,
   6-8 cartel,9 poste,10-13 columna (sola/arriba/medio/abajo),14 pinchos,15 roca,16 llave */
static u8 tileidx(short x,short y){
  u8 c=g[y][x], up, dn;
  switch(c){ case '$': return 0; case '#': return 1; case 'H': return 2; case '-': return 3;
    case 'D': return haskey?5:4; case 'k': return 16; case 'a': return 6; case 'b': return 7; case 'c': return 8; case 'p': return 9; case '^': return 14; case 'r': return 15;
    case '=': up=(y>0&&g[y-1][x]=='='); dn=(y<GH-1&&g[y+1][x]=='=');   /* columna: capitel, fuste, base */
      return up?(dn?12:13):(dn?11:10); }
  return 99;
}

/* ---------- pixeles sueltos sobre el buffer de una celda (8x12 px = 2 bytes por linea) ---------- */
static void setpx(u8*b,u8 x,u8 y,u8 c){
  u8 *w=&b[(y<<1)+(x>>2)], k=x&3, m=(u8)(0x88>>k), v=*w&~m;
  if(c&1) v|=(u8)(0x80>>k);
  if(c&2) v|=(u8)(0x08>>k);
  *w=v;
}
static void ovp(u8*b,short cx,short y0,short wx,short wy,u8 c){
  short x=wx-(cx<<3), y=wy-y0;
  if(x>=0&&x<8&&y>=0&&y<12) setpx(b,(u8)x,(u8)y,c);
}
static void star(u8*b,short cx,short y0,short bx,short by,u8 c){
  if((bx>>2)&1){ ovp(b,cx,y0,bx,by-1,c); ovp(b,cx,y0,bx+2,by-1,c); ovp(b,cx,y0,bx+1,by,c); ovp(b,cx,y0,bx,by+1,c); ovp(b,cx,y0,bx+2,by+1,c); }
  else { ovp(b,cx,y0,bx+1,by-1,c); ovp(b,cx,y0,bx,by,c); ovp(b,cx,y0,bx+1,by,c); ovp(b,cx,y0,bx+2,by,c); ovp(b,cx,y0,bx+1,by+1,c); }
}
static void arms(u8*b,short cx,short y0,short px,short gy){   /* brazos a ambos lados, siempre visibles */
  short k;
  for(k=0;k<3;k++){ ovp(b,cx,y0,px+k,gy,P_W); ovp(b,cx,y0,px+5+k,gy,P_W); }
  ovp(b,cx,y0,px+2,gy+1,P_W); ovp(b,cx,y0,px+5,gy+1,P_W);
}
static u8 pose_p(void){
  if(p.prone) return 4;
  if(cell(p.x,p.y)=='-') return (p.a&1)?2:3;
  if(cell(p.x,p.y)=='H') return (p.a&1)?2:3;
  return ((p.a&1)&&p.moving)?1:0;
}
static u8 pose_e(En*e){
  if(cell(e->x,e->y)=='H') return (e->a&1)?2:3;
  return (e->a&1)?1:0;
}
static short pjy(void){ return p.air? JY[p.air]:0; }

#ifdef HOST_STATS
static unsigned long host_cells;
#endif
static void draw_cell(short cx,short cy){
  u8 b[24]; u8 r,i,t,n; short y0=(cy<<3)+(cy<<2), ro, rr, sy, jy, gx, gy, bx;
  const u8 *dp,*mp; volatile u8*d; u8*bp;
#ifdef HOST_STATS
  host_cells++;
#endif
  t=tileidx(cx,cy);
  bp=b; r=24;
  if(t<17){ dp=TILES+o24(t); do{ *bp++=*dp++; }while(--r); } else { do{ *bp++=0; }while(--r); }
  /* jugador */
  jy=pjy();
  if(p.x==cx){ ro=(p.y<<3)+(p.y<<2)+jy-y0;
    if(ro>-12&&ro<12){ n=(pose_p()<<1)+(p.face<0); dp=PLD+o24(n); mp=PLM+o24(n);
      for(sy=0;sy<12;sy++){ rr=ro+sy;
        if(rr>=0&&rr<12){ b[rr<<1]=(b[rr<<1]&~mp[sy<<1])|dp[sy<<1]; b[(rr<<1)+1]=(b[(rr<<1)+1]&~mp[(sy<<1)+1])|dp[(sy<<1)+1]; } } } }
  if((p.x==cx||p.x==cx-1||p.x==cx+1)&&cell(p.x,p.y)!='H'&&cell(p.x,p.y)!='-'&&!p.prone){
    gx=p.x<<3; gy=(p.y<<3)+(p.y<<2)+5+jy;
    arms(b,cx,y0,gx,gy);
    if(p.swing) ovp(b,cx,y0,p.face>0?gx+8:gx-1,gy,P_Y);   /* fogonazo hacia donde mira */
  }
  for(i=0;i<2;i++) if(pb[i].on&&rowof[pb[i].y]==cy){ bx=pb[i].xf>>2; if((bx>>3)<=cx&&((bx+2)>>3)>=cx) star(b,cx,y0,bx,pb[i].y,P_W); }
  for(i=0;i<4;i++) if(eb[i].on&&rowof[eb[i].y]==cy){ bx=eb[i].xf>>2; if((bx>>3)<=cx&&((bx+2)>>3)>=cx) star(b,cx,y0,bx,eb[i].y,P_R); }
  for(i=0;i<nen;i++) if(en[i].x==cx&&!en[i].dead){
    if(en[i].y==cy){ n=(pose_e(&en[i])<<2)+((en[i].hat&1)<<1)+(en[i].face<0); dp=END+o24(n); mp=ENM+o24(n);
      for(r=0;r<24;r++) b[r]=(b[r]&~mp[r])|dp[r]; }
    if(en[i].y==cy&&cell(en[i].x,en[i].y)!='H'){
      gy=(en[i].y<<3)+(en[i].y<<2)+5;
      arms(b,cx,y0,cx<<3,gy); }
  }
  for(r=0;r<12;r++){ d=VRAM+lineoff[y0+YOFF+r]+GX+(cx<<1); d[0]=b[r<<1]; d[1]=b[(r<<1)+1]; }
}

/* ---------- repintado selectivo ---------- */
typedef struct{ short x0,y0,x1,y1; u16 sig; u8 v; } Sl;
static Sl sl[15];
static void markrc(Sl*s){
  short x0=s->x0,y0=s->y0,x1=s->x1,y1=s->y1,cx,cy;
  if(x0<0)x0=0; if(y0<0)y0=0; if(x1>223)x1=223; if(y1>GH*12-1)y1=GH*12-1;
  if(x1<x0||y1<y0) return;
  for(cy=rowof[y0];cy<=rowof[y1];cy++) for(cx=x0>>3;cx<=(x1>>3);cx++) markcell(cx,cy);
}
static void setslot(u8 i,u8 v,short x0,short y0,short x1,short y1,u16 sig){
  Sl*s=&sl[i];
  if(!v){ if(s->v){ markrc(s); s->v=0; } return; }
  if(s->v&&s->x0==x0&&s->y0==y0&&s->x1==x1&&s->y1==y1&&s->sig==sig) return;
  if(s->v) markrc(s);
  s->x0=x0; s->y0=y0; s->x1=x1; s->y1=y1; s->sig=sig; s->v=1; markrc(s);
}
static void render(void){
  short i,cx,cy,px,py,jy,m,bx; u16 sig;
  px=p.x<<3; py=(p.y<<3)+(p.y<<2); jy=pjy(); m=p.swing?1:0;
  sig=pose_p()|((u16)(p.face<0)<<3)|((u16)p.air<<4)|((u16)m<<8);
  setslot(0,1,px-m,py+jy,px+7+m,py+11+jy,sig);
  for(i=0;i<8;i++){
    if(i<nen&&!en[i].dead){ px=en[i].x<<3; py=(en[i].y<<3)+(en[i].y<<2);
      setslot(1+i,1,px,py,px+7,py+11,pose_e(&en[i])|((u16)(en[i].face<0)<<3)|((u16)(en[i].hat&1)<<4)); }
    else setslot(1+i,0,0,0,0,0,0);
  }
  for(i=0;i<2;i++){ if(pb[i].on){ bx=pb[i].xf>>2; setslot(9+i,1,bx,pb[i].y-1,bx+2,pb[i].y+1,(u16)((bx>>2)&1)); } else setslot(9+i,0,0,0,0,0,0); }
  for(i=0;i<4;i++){ if(eb[i].on){ bx=eb[i].xf>>2; setslot(11+i,1,bx,eb[i].y-1,bx+2,eb[i].y+1,(u16)((bx>>2)&1)); } else setslot(11+i,0,0,0,0,0,0); }
  for(i=0;i<ndirty;i++){ cx=dlist[i]&31; cy=dlist[i]>>5; dirty[cy][cx]=0; draw_cell(cx,cy); }
  ndirty=0;
}

/* ---------- texto (fuente 3x5) y elementos fijos de pantalla ---------- */
static void plot(short x,short y,u8 c){
  volatile u8*a; u8 k,m,v;
  if(x<0||x>319||y<0||y>199) return;
  a=VRAM+lineoff[y]+(x>>2); k=x&3; m=(u8)(0x88>>k); v=*a&~m;
  if(c&1) v|=(u8)(0x80>>k);
  if(c&2) v|=(u8)(0x08>>k);
  *a=v;
}
static void putch(short x,short y,char ch,u8 col,u8 sc){
  u8 i; short r,c,bx,by; u16 bits=0;
  for(i=0;FONT_CH[i];i++) if(FONT_CH[i]==ch){ bits=FONT_BITS[i]; break; }
  if(!bits) return;
  for(r=0;r<5;r++) for(c=0;c<3;c++) if((bits>>(14-(r*3+c)))&1)
    for(by=0;by<sc;by++) for(bx=0;bx<sc;bx++) plot(x+c*sc+bx,y+r*sc+by,col);
}
static short puts_(short x,short y,const char*s,u8 col,u8 sc){ for(;*s;s++){ putch(x,y,*s,col,sc); x+=sc*4; } return x; }
static void num(char*o,u16 n,u8 digits){
  static const u16 pw[5]={10000,1000,100,10,1}; u8 i,d;
  for(i=5-digits;i<5;i++){ d=0; while(n>=pw[i]){ n-=pw[i]; d++; } *o++='0'+d; } *o=0;
}
static void hlch(short x,short y,char ch,u8 sc){   /* brillo: esquina de cada pixel grande */
  u8 i; short r,c; u16 bits=0;
  for(i=0;FONT_CH[i];i++) if(FONT_CH[i]==ch){ bits=FONT_BITS[i]; break; }
  if(!bits) return;
  for(r=0;r<5;r++) for(c=0;c<3;c++) if((bits>>(14-(r*3+c)))&1) plot(x+c*sc,y+r*sc,P_W);
}
static void clrbytes(u8 bx,short y,u8 nb,short rows){   /* borra un rectangulo alineado a bytes (4 px) */
  volatile u8*a; u8 j; short r;
  for(r=0;r<rows;r++){ a=VRAM+lineoff[y+r]+bx; for(j=0;j<nb;j++) a[j]=0; }
}
static void draw_title(void){
  short x,i; const char*t="EL RONINGASA RONIN";
  x=48; for(i=0;t[i];i++){ putch(x+1,1,t[i],P_R,2); x+=8; }      /* sombra */
  x=48; for(i=0;t[i];i++){ putch(x,0,t[i],P_Y,2); x+=8; }        /* letras amarillas */
  x=48; for(i=0;t[i];i++){ hlch(x,0,t[i],2); x+=8; }             /* brillo blanco */
  for(x=GX*4;x<GX*4+224;x++) plot(x,11,P_W);                     /* linea blanca bajo el titulo */
  for(i=0;i<200;i++) plot(236,i,P_W);                            /* separador de la barra lateral */
}
static u16 ls; static u8 lg,lab_dirty,lc; static s8 ll;
static void clrf(short x,u8 npx){ clrbytes((u8)(x>>2),HUDY,(u8)(npx>>2),5); }   /* campo numerico (x multiplo de 4) */
static void draw_cjk(void){                  /* 7 caracteres 24x24 en dos columnas de la barra lateral */
  u8 n,r,xb,k; short y,x,x0;
  for(n=0;n<7;n++){
    if(n<4){ x0=SIDEX+4; y=4+n*38; } else { x0=SIDEX+40; y=23+(n-4)*38; }
    for(r=0;r<24;r++) for(xb=0;xb<3;xb++){ u8 v=CJK[n][r*3+xb];
      for(k=0;k<8;k++) if((v>>(7-k))&1){ x=x0+xb*8+k; plot(x+1,y+r+1,P_R); plot(x,y+r,P_Y); } }
  }
}
static void draw_counters(void){            /* solo repinta lo que ha cambiado */
  char t[8]; hud_dirty=0;
  if(lab_dirty){ lab_dirty=0; clrbytes(GX,HUDY-1,56,7);
    puts_(16,HUDY,"PUNTOS ",P_W,1); puts_(72,HUDY,"MONEDAS ",P_W,1); puts_(120,HUDY,"VIDAS ",P_W,1); puts_(160,HUDY,"NIVEL ",P_W,1);
    ls=0xFFFF; lg=255; ll=-100; lvl_last=255; }
  if(score!=ls){ ls=score; clrf(44,20); num(t,score,5); puts_(44,HUDY,t,P_Y,1); }
  if(coins!=lg){ lg=coins; clrf(104,8); num(t,coins,2); puts_(104,HUDY,t,P_Y,1); }
  if(lvl!=lvl_last){ lvl_last=lvl; clrf(184,8); num(t,lvl+1,2); puts_(184,HUDY,t,P_Y,1); }
  if(lives!=ll||cheat!=lc){ ll=lives; lc=cheat; clrf(144,12);
    if(cheat) puts_(144,HUDY,"INF",P_Y,1); else { num(t,lives<0?0:lives,2); puts_(144,HUDY,t,P_Y,1); } }
}
static void draw_msg(void){                  /* mensajes en la barra lateral, bajo los kanji */
  msg_dirty=0; clrbytes(SIDEX>>2,148,20,52);
  if(state==0){
    if(haskey){ puts_(SIDEX,152,"LLAVE CONSEGUIDA",P_Y,1); puts_(SIDEX,160,"VE A LA PUERTA",P_Y,1); }
    else { puts_(SIDEX,152,"BUSCA LA LLAVE",P_Y,1); puts_(SIDEX,160,"PARA LA PUERTA",P_Y,1); }
    puts_(SIDEX,176,"ESPACIO ESTRELLA",P_W,1); puts_(SIDEX,184,"ESC SALIR",P_W,1); }
  else if(state==1){ if(lvl<NLEV-1){ puts_(SIDEX,160,"NIVEL SUPERADO",P_Y,1); puts_(SIDEX,170,"SIGUIENTE NIVEL",P_W,1); }
    else { puts_(SIDEX,160,"VICTORIA TOTAL",P_Y,1); puts_(SIDEX,170,"ENTER REINICIA",P_W,1); } }
  else { puts_(SIDEX,160,"FIN DE PARTIDA",P_R,1); puts_(SIDEX,170,"ENTER REINICIA",P_W,1); }
}

/* ---------- logica (identica a la version de QL) ---------- */
static u8 lbuf[GH*GW];                       /* nivel descomprimido */
static void unpack(u8 n){                    /* RLE: literal; si le sigue un byte con bit 7, es el total de repeticiones */
  const u8*s=LEVRLE+LEVOFF[n]; u16 i=0; u8 c,k;
  while(i<GH*GW){ c=*s++; lbuf[i++]=c;
    if(*s&0x80){ k=*s++&0x7F; while(--k&&i<GH*GW) lbuf[i++]=c; } }
}
static void load(u8 full){
  short x,y; u8 c; En*e; u16 li=0;
  nen=0; haskey=0;
  for(x=0;x<2;x++) pb[x].on=0;
  for(x=0;x<4;x++) eb[x].on=0;
  for(x=0;x<15;x++) sl[x].v=0;
  unpack(lvl);
  for(y=0;y<GH;y++) for(x=0;x<32;x++){ c=(x<GW)?lbuf[li++]:' '; g[y][x]=c;
    if(c=='P'){ p.x=p.sx=x; p.y=p.sy=y; g[y][x]=' '; }
    else if(c=='E'||c=='F'){ e=&en[nen]; e->x=e->sx=x; e->y=e->sy=y; e->dir=e->face=(c=='E')?1:-1;
      e->a=0; e->cd=0; e->dead=0; e->hat=nen&3; nen++; g[y][x]=' '; }
    else if(c=='D'){ doorx=x; doory=y; } }
  p.face=1; p.a=0; p.air=0; p.jl=0; p.prone=0; p.swing=0; p.moving=0; digdir=0;
  if(full){ score=0; lives=3; coins=0; }
  { u8 th=(lvl<8)?0:lvl-7; if(th!=theme){ theme=th; setink(P_R,THEMEINK[th]); } }
  state=0; markall(); hud_dirty=1; msg_dirty=1; lab_dirty=1;
}
static void die(void){
  u8 i;
  if(state!=0) return;
  if(!cheat){ lives--; hud_dirty=1; if(lives<=0){ state=2; msg_dirty=1; return; } }
  p.x=p.sx; p.y=p.sy; p.air=0; p.prone=0;
  for(i=0;i<2;i++) pb[i].on=0;
  for(i=0;i<4;i++) eb[i].on=0;
  for(i=0;i<nen;i++){ en[i].x=en[i].sx; en[i].y=en[i].sy; }
}
static void hit(void){
  u8 i;
  if(state!=0||p.air) return;
  for(i=0;i<nen;i++) if(!en[i].dead&&en[i].x==p.x&&en[i].y==p.y){ die(); return; }
}
static void player_tick(u8 keys){
  u8 l=(keys&2)!=0, r=(keys&16)!=0, u=(keys&4)!=0, d=(keys&128)!=0, i; short dx;
  p.a++; if(p.swing) p.swing--; if(p.air) p.air--;
  p.moving=(keys&(2|4|16|128|64))!=0;
  if(!p.air&&!supported(p.x,p.y)){ p.y++; p.prone=0; }
  else {
    if(!u) p.jl=0; else { if(!p.jl&&cell(p.x,p.y)!='H'&&!p.air&&solid(p.x,p.y+1)){ dx=l?-1:(r?1:p.face);
      if(cell(p.x,p.y-1)=='-') p.y--;
      else if(cell(p.x+dx,p.y)=='r'&&!solid(p.x,p.y-1)&&!solid(p.x+dx,p.y-1)){ p.x+=dx; p.y--; p.face=dx; p.air=2; l=r=u=d=0; }   /* salta de roca en roca */
      else p.air=4; } p.jl=1; }
    p.prone=d&&cell(p.x,p.y)!='H'&&solid(p.x,p.y+1)&&!p.air;
    if(digdir){
      p.swing=3;
      if(!solid(p.x+digdir,p.y)) for(i=0;i<2;i++) if(!pb[i].on){
        pb[i].xf=((p.x<<3)+(digdir>0?7:0))<<2; pb[i].y=(p.y<<3)+(p.y<<2)+(p.prone?9:5); pb[i].d=digdir; pb[i].on=1; break; }
      digdir=0;
    } else if(l||r){ dx=r?1:-1; p.face=dx; if(!p.prone&&!solid(p.x+dx,p.y)) p.x+=dx; }
    else if(u){ if(cell(p.x,p.y)=='H'&&cell(p.x,p.y-1)=='H') p.y--; }
    else if(d){ if(!solid(p.x,p.y+1)) p.y++; }
  }
  if(p.y>=GH-1||cell(p.x,p.y)=='^'){ die(); }                             /* foso del suelo: mortal */
  if(cell(p.x,p.y)=='$'){ g[p.y][p.x]=' '; markcell(p.x,p.y); coins++; score+=100; hud_dirty=1;
    if(coins>=50){ coins=0; if(lives<99) lives++; } }          /* 50 monedas = una vida */
  if(cell(p.x,p.y)=='k'){ g[p.y][p.x]=' '; markcell(p.x,p.y); haskey=1; markcell(doorx,doory); hud_dirty=1; msg_dirty=1; }   /* la llave abre la puerta */
  if(state==0&&haskey&&cell(p.x,p.y)=='D'){ state=1; score+=500; hud_dirty=1; msg_dirty=1; }
  hit();
}
static void enemy_tick(void){
  u8 i,j,clear; short dr,c,nx; En*e;
  for(i=0;i<nen;i++){ e=&en[i]; e->a++; if(e->dead) continue;
    if(e->cd) e->cd--;
    else if(e->y==p.y){ dr=(p.x>e->x)?1:((p.x<e->x)?-1:0); clear=dr!=0;
      for(c=e->x+dr;clear&&c!=p.x;c+=dr) if(solid(c,e->y)) clear=0;
      if(clear) for(j=0;j<4;j++) if(!eb[j].on){ e->face=dr;
        eb[j].xf=((e->x<<3)+(dr>0?7:0))<<2; eb[j].y=(e->y<<3)+(e->y<<2)+5; eb[j].d=dr; eb[j].on=1;
        e->cd=12+(rnd()&7); break; } }
    if(!supported(e->x,e->y)){ e->y++; continue; }
    nx=e->x+e->dir;
    if(solid(nx,e->y)||!supported(nx,e->y)){ e->dir=-e->dir; nx=e->x+e->dir; }
    if(!solid(nx,e->y)&&supported(nx,e->y)){ e->x=nx; e->face=e->dir; }
  }
  hit();
}
static void bullet_tick(void){
  u8 i,j,hitp=0; short bx,cx,cy;
  for(i=0;i<2;i++) if(pb[i].on){
    pb[i].xf+=pb[i].d*10; bx=pb[i].xf>>2;
    if(bx<0||bx>=224){ pb[i].on=0; continue; }
    cx=bx>>3; cy=rowof[pb[i].y];
    if(solid(cx,cy)){ pb[i].on=0; continue; }
    for(j=0;j<nen;j++) if(!en[j].dead&&en[j].x==cx&&en[j].y==cy){ en[j].dead=1; score+=200; hud_dirty=1; pb[i].on=0; break; }
  }
  for(i=0;i<4;i++) if(eb[i].on){
    eb[i].xf+=eb[i].d*5; bx=eb[i].xf>>2;
    if(bx<0||bx>=224){ eb[i].on=0; continue; }
    cx=bx>>3; cy=rowof[eb[i].y];
    if(solid(cx,cy)){ eb[i].on=0; continue; }
    if(cx==p.x&&cy==p.y&&!p.air&&!p.prone){ hitp=1; eb[i].on=0; }
  }
  if(hitp) die();
}

/* ---------- bucle principal ---------- */
static u8 pk,fc,ec,wc;
static void game_init(void){
  u8 cnt=0,r=0,rr=0; short y,b=0,ln;
  rs=0xACE1; lvl=STARTLVL; lvl_last=255; lab_dirty=1; theme=255;
  cheat=cidx=cprev=0; pk=fc=ec=wc=0; state=0; ndirty=0; lc=0; ll=0; lg=0; ls=0;
  fw(KM_DISARM_BREAK,0,0,0); flushkeys();           /* ESC ya no interrumpe el programa */
  fw(SCR_SET_MODE,1,0,0);                           /* Mode 1 (borra la pantalla) */
  setink(0,0); setink(P_W,26); setink(P_R,THEMEINK[0]); setink(P_Y,24); fw(SCR_SET_BORDER,0,0,0);
  for(ln=0;ln<200;ln++){ lineoff[ln]=((u16)rr<<11)+b; if(++rr==8){ rr=0; b+=80; } }   /* direcciones de linea del CPC */
  for(y=0;y<GH*12;y++){ rowof[y]=r; if(++cnt==12){ cnt=0; r++; } }
  load(1); draw_title(); draw_cjk();
}
static void game_exit(void){
  flushkeys(); fw(KM_ARM_BREAK,0,0,0); fw(SCR_RESET,0,0,0); fw(SCR_SET_MODE,1,0,0);
}
/* un fotograma; devuelve 1 si hay que salir */
static u8 game_frame(void){
  u8 k;
  sync(); k=readkeys(); cheat_scan();
  if(k&8) return 1;                                  /* ESC: salir al BASIC */
  if((k&64)&&!(pk&64)) digdir=p.face;                 /* ESPACIO: disparar */
  if(state==0){
    bullet_tick();
    if(++fc>=4){ fc=0; player_tick(k); }
    if(++ec>=11){ ec=0; enemy_tick(); }
  } else if(state==1&&lvl<NLEV-1){                    /* puerta cruzada: siguiente nivel solo (1,5 s) */
    if(++wc>=75||((k&1)&&!(pk&1))){ wc=0; lvl++; load(0); }
  } else if((k&1)&&!(pk&1)){ lvl=0; load(1); }
  pk=k;
  render();
  if(hud_dirty) draw_counters();
  if(msg_dirty) draw_msg();
  return 0;
}
#ifndef NOMAIN
int main(void){
  game_init();
  while(!game_frame()) ;
  game_exit();
  return 0;
}
#endif
