/* Pruebas en el PC: compila game.c tal cual (con -DHOST) y sustituye solo el firmware del CPC. */
#define HOST
#define NOMAIN
#define HOST_STATS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "game.c"

static u8 hostkey[80]; static u8 pal[4]; static u8 mode_set; static unsigned chars_pending;
void fwcall(void){
  switch(fw_addr){
    case KM_TEST_KEY: fw_af = hostkey[(fw_af>>8)&127] ? 0x0000 : 0x0040; break;   /* NZ = pulsada */
    case KM_READ_CHAR: fw_af = 0; break;                                          /* sin caracteres */
    case SCR_SET_MODE: mode_set=(u8)(fw_af>>8); memset(vram,0,sizeof vram); break;
    case SCR_SET_INK: pal[(fw_af>>8)&3]=(u8)(fw_bc>>8); break;
    default: break;
  }
}
static const u8 INK[27][3]={{0,0,0},{0,0,128},{0,0,255},{128,0,0},{128,0,128},{128,0,255},{255,0,0},{255,0,128},{255,0,255},
 {0,128,0},{0,128,128},{0,128,255},{128,128,0},{128,128,128},{128,128,255},{255,128,0},{255,128,128},{255,128,255},
 {0,255,0},{0,255,128},{0,255,255},{128,255,0},{128,255,128},{128,255,255},{255,255,0},{255,255,128},{255,255,255}};
static void shot(const char*name){
  FILE*f=fopen(name,"wb"); int x,y; fprintf(f,"P6\n320 200\n255\n");
  for(y=0;y<200;y++) for(x=0;x<320;x++){ u8 v=vram[lineoff[y]+(x>>2)]; int k=x&3, pen=((v>>(7-k))&1)|(((v>>(3-k))&1)<<1);
    fwrite(INK[pal[pen]],1,3,f); }
  fclose(f);
}
static int fails;
#define CHECK(c,...) do{ if(!(c)){ printf("FALLO: " __VA_ARGS__); printf("\n"); fails++; } else { printf("ok:    " __VA_ARGS__); printf("\n"); } }while(0)
static void frames(int n){ while(n--) game_frame(); }
static void setk(int up,int dn,int l,int r,int fire){ hostkey[0]=up; hostkey[2]=dn; hostkey[8]=l; hostkey[1]=r; hostkey[47]=fire; }
static void release(void){ memset(hostkey,0,sizeof hostkey); }
static void fresh(int level){ release(); game_init(); lvl=level; load(1); frames(2); }
static int freecell(int x,int y){ return x>=0&&x<GW&&(g[y][x]==' '||g[y][x]=='$'||g[y][x]=='k')&&y+1<GH&&(g[y+1][x]=='#'||g[y+1][x]=='='||g[y+1][x]=='r'); }
static void tele(int x,int y){ p.x=x; p.y=y; p.air=0; }
static void kill_enemies(void){ int i; for(i=0;i<nen;i++) en[i].dead=1; }

int main(int argc,char**argv){
  int n,i,k; unsigned long seed=12345;
  /* ---- 1. capturas de los 19 niveles ---- */
  for(n=0;n<NLEV;n++){ char nm[64]; fresh(n); frames(3); sprintf(nm,"shot_l%02d.ppm",n+1); shot(nm); }
  fresh(0); frames(2); shot("shot_start.ppm");
  /* ---- 2. mecanicas ---- */
  { int x,y,gx=-1,gy=-1,dir=0;                       /* moneda 50 = vida */
    fresh(0); kill_enemies();
    for(y=0;y<GH&&gx<0;y++) for(x=0;x<GW;x++) if(g[y][x]=='$'){ gx=x; gy=y; break; }
    if(freecell(gx-1,gy)){ tele(gx-1,gy); dir=1; } else { tele(gx+1,gy); dir=-1; }
    coins=49; { int l0=lives, s0=score; setk(0,0,dir<0,dir>0,0); frames(5); release();
      CHECK(coins==0 && lives==l0+1 && score==s0+100,"moneda 50: monedas=%d vidas %d->%d puntos %d->%d",coins,l0,lives,s0,score); } }
  { int x,y,kx=-1,ky=-1,dir=0;                       /* llave y puerta */
    fresh(0); kill_enemies();
    for(y=0;y<GH&&kx<0;y++) for(x=0;x<GW;x++) if(g[y][x]=='k'){ kx=x; ky=y; break; }
    if(freecell(kx-1,ky)){ tele(kx-1,ky); dir=1; } else { tele(kx+1,ky); dir=-1; }
    setk(0,0,dir<0,dir>0,0); frames(40); release();
    CHECK(haskey==1,"llave recogida (haskey=%d)",haskey);
    tele(26,1); setk(0,0,0,1,0); frames(40); release();
    CHECK(state==1,"cruzar la puerta con llave -> nivel superado (state=%d)",state);
    fresh(0); kill_enemies(); tele(26,1); setk(0,0,0,1,0); frames(60); release();
    CHECK(state==0,"puerta sin llave no abre (state=%d)",state); }
  { fresh(0); kill_enemies(); tele(2,13); setk(0,0,0,1,0); frames(20); release(); CHECK(p.x>2,"andar a la derecha (x=%d)",p.x);
    setk(0,0,0,0,1); frames(1); release(); frames(2); { int on=pb[0].on||pb[1].on; CHECK(on,"disparar crea una estrella"); } }
  { fresh(0); { int l0=lives; for(i=0;i<nen;i++) if(!en[i].dead){ tele(en[i].x,en[i].y); break; } hit(); CHECK(lives==l0-1 || state==2,"contacto con enemigo resta vida (%d->%d)",l0,lives); } }
  { fresh(0); lives=1; kill_enemies(); tele(2,14); player_tick(0); CHECK(state==2,"caer al foso con ultima vida -> fin de partida (state=%d)",state);
    setk(0,0,0,0,0); hostkey[6]=1; frames(2); hostkey[6]=0; frames(2); CHECK(state==0&&lives==3&&lvl==0,"ENTER reinicia (state=%d vidas=%d)",state,lives); }
  { fresh(0); static const int seq[6]={67,59,58,50,51,43}; for(i=0;i<6;i++){ hostkey[seq[i]]=1; frames(2); hostkey[seq[i]]=0; frames(2); }
    CHECK(cheat==1,"truco QWERTY (cheat=%d)",cheat); }
  /* ---- 3. fuzz: teclas aleatorias en todos los niveles; ASAN/UBSAN vigilan los limites ---- */
  { unsigned long total=0, worst=0; int worstn=0; unsigned long fr=0;
    for(n=0;n<NLEV;n++){ fresh(n);
      for(i=0;i<4000;i++){
        if((i%7)==0){ seed=seed*1103515245UL+12345UL; k=(seed>>16)&31; release();
          if(k&1) hostkey[8]=1; if(k&2) hostkey[1]=1; if(k&4) hostkey[0]=1; if(k&8) hostkey[2]=1; if(k&16) hostkey[47]=1; }
        { unsigned long c0=host_cells; game_frame(); { unsigned long c=host_cells-c0; total+=c; fr++; if(c<400&&c>worst&&i>20){ worst=c; worstn=n; } } }
        if(state!=0 && (i%50)==0){ hostkey[6]=1; } else hostkey[6]=0;
        if(ndirty>GW*GH){ printf("ndirty desbordado\n"); fails++; }
      } }
    printf("fuzz: %lu fotogramas, media %.1f celdas/fotograma, maximo %lu en regimen normal (nivel %d; los repintados completos de 420 al cambiar de nivel no cuentan)\n",fr,(double)total/fr,worst,worstn+1);
    CHECK(1,"fuzz de %d niveles sin errores de memoria (ver sanitizers)",NLEV); }
  printf("\n%s (%d fallos)\n",fails?"HAY FALLOS":"TODO OK",fails);
  (void)argc; (void)argv;
  return fails!=0;
}
