; crt0 para SDCC (sdasz80) - programa binario de Amstrad CPC cargado en 0x4000.
; El firmware y las interrupciones siguen activos; se vuelve al BASIC con RET.
	.module	crt0
	.globl	_main
	.globl	_fwcall
	.globl	_fw_addr
	.globl	_fw_af
	.globl	_fw_bc
	.globl	_fw_de
	.globl	_fw_hl

	.area	_HOME
	.area	_CODE
	.area	_INITIALIZER
	.area	_GSINIT
	.area	_GSFINAL
	.area	_DATA
	.area	_INITIALIZED
	.area	_BSEG
	.area	_BSS
	.area	_HEAP

	.area	_CODE
_start::
	push	ix
	push	iy
	; poner a cero toda el area _DATA (variables estaticas sin inicializador)
	ld	bc, #l__DATA
	ld	a, b
	or	a, c
	jr	Z, 1$
	ld	hl, #s__DATA
	ld	e, l
	ld	d, h
	inc	de
	dec	bc
	ld	(hl), #0
	ld	a, b
	or	a, c
	jr	Z, 1$
	ldir
1$:
	call	gsinit
	call	_main
	pop	iy
	pop	ix
	ret

; _fwcall: llama a la rutina de firmware en (_fw_addr) con los registros A,BC,DE,HL de las variables
; _fw_*, y devuelve en ellas los registros resultantes (_fw_af: bajo = F, alto = A).
_fwcall::
	push	ix
	push	iy
	ld	ix, (_fw_addr)
	ld	a, (_fw_af + 1)
	ld	bc, (_fw_bc)
	ld	de, (_fw_de)
	ld	hl, (_fw_hl)
	call	_fwjump
	ld	(_fw_hl), hl
	ld	(_fw_bc), bc
	ld	(_fw_de), de
	push	af
	pop	hl
	ld	(_fw_af), hl
	pop	iy
	pop	ix
	ret
_fwjump:
	jp	(ix)

	.area	_GSINIT
gsinit::
	ld	bc, #l__INITIALIZER
	ld	a, b
	or	a, c
	jr	Z, gsinit_next
	ld	de, #s__INITIALIZED
	ld	hl, #s__INITIALIZER
	ldir
gsinit_next:
	.area	_GSFINAL
	ret
