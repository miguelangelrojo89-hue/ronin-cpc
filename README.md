# El Roningasa Ronin — port para Amstrad CPC (464 / 664 / 6128)

Port del juego de QL a Z80. Misma lógica, mismos 19 niveles (los genera `levels.py`, con su solver), mismo
truco QWERTY. Funciona en cualquier CPC con disquetera; no necesita los 128 KB del 6128 (usa unos 20 KB).

## Cómo se juega
| Acción | Teclas |
|---|---|
| Moverse / subir escaleras / tumbarse | cursores o joystick |
| Saltar | cursor arriba (también salta de roca en roca) |
| Lanzar estrella | ESPACIO o botón del joystick |
| Reiniciar tras fin de partida / saltar pantalla de nivel | ENTER o RETURN |
| Salir al BASIC | ESC |

Objetivo: coge la llave y cruza la puerta. 50 monedas = una vida. Teclear Q W E R T Y = vidas infinitas.

## Compilar (necesitas SDCC ≥ 4.0 y Python 3)
    python3 build.py        # genera ronin.dsk y RONIN.BIN
    python3 build.py test   # pruebas en el PC (gcc): lógica + fuzzing con ASan/UBSan + capturas
    python3 build.py pack   # prueba del empaquetado AMSDOS/DSK
En el CPC / emulador: `RUN"RONIN.BIN"`.

## Qué cambia respecto al QL
- **Pantalla**: Mode 1 (320x200, 4 plumas). Cabe el tablero de 28x15 celdas de 8x12 px (224x180) más una barra
  lateral con los kanji 浪人忍者武士道 y los mensajes. Marcadores bajo el tablero, título arriba.
- **Colores**: solo 4 plumas → negro, blanco, amarillo y una pluma de «tema» cuya tinta cambia en cada nivel
  (ladrillos, escaleras, pecho/piernas…). Los 4 sombreros de enemigo pasan a 2 variantes.
- **Sprites**: prepaquetados en formato Mode 1 con máscara por `gen_cpc.py` (en el QL se empaquetaban al arrancar).
- **Entrada y vídeo**: por el firmware (`KM TEST KEY`, `MC WAIT FLYBACK`, `SCR SET MODE/INK`); todo pasa por un
  único trampolín `fwcall()` en `crt0.s`. Memoria de vídeo escrita directamente en &C000.
- **Temporización**: igual que el QL (50 Hz; jugador cada 4 fotogramas, enemigos cada 11).
- La lógica de `game.c` (movimiento, enemigos, disparos, niveles) es la misma que la del QL, línea por línea.

## Qué está verificado y qué no
Verificado en el PC (mismo `game.c`, solo se sustituye el firmware):
- Mecánicas: moneda 50 = vida, llave y puerta, puerta cerrada sin llave, andar, disparar, morir, game over, reinicio, truco.
- 76.000 fotogramas con teclas aleatorias en los 19 niveles bajo AddressSanitizer + UBSan, sin errores.
  En régimen normal se repintan de media ~3 celdas por fotograma (máximo 23); el repintado completo de 420 celdas
  solo ocurre al cambiar de nivel.
- Capturas de los 19 niveles (ver `montaje.png`): empaquetado Mode 1, máscaras, temas, HUD y kanji correctos.
- Empaquetado: .ihx → binario → cabecera AMSDOS → .dsk, releído con un lector independiente (1 y 2 extents).

**No verificado** (no había compilador Z80 ni emulador de CPC disponibles al escribirlo):
1. La compilación con SDCC y el tamaño real del binario (`build.py` avisa si invade el área de variables).
2. Las llamadas al firmware: sobre todo `KM TEST KEY` (se asume Z=0 ⇒ tecla pulsada) y los números de tecla
   (joystick 72-77). Si el teclado va invertido o no responde, es lo primero que hay que mirar (`keydown()` en `game.c`).
3. Los offsets de la cabecera AMSDOS y el directorio del .dsk siguen el formato estándar, pero solo se han probado contra
   mi propio lector. Si el CPC no carga el fichero desde el .dsk, prueba a copiar `RONIN.BIN` con otra herramienta (iDSK, CPCDiskXP).
4. Rendimiento real en Z80 a 4 MHz. Con ~3 celdas por fotograma debería ir sobrado, pero no está medido.

## Ficheros
`game.c` juego · `crt0.s` arranque y trampolín al firmware · `gen_cpc.py` genera `data.h` · `assets.py`, `levels.py`,
`cjk_data.py` datos del original · `cpcpack.py` AMSDOS/DSK · `build.py` · `test_host.c`, `test_pack.py` pruebas.
