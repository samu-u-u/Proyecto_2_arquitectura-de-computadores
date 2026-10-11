# =============================================================
# game.s — Juego de reflejos sobre Pochoco SoC (RV32E)
# Proyecto 2 - Arquitectura de Computadores
#
# Reloj: 25 MHz (Go Board)
#   1 décima de segundo =  2.500.000 ciclos
#   3 segundos           = 75.000.000 ciclos
#
# Mapa de periféricos (base 0x8000_0000):
#   0x00 displays 7-seg (W)     0x04 LEDs (W)
#   0x08 botones (R)            0x0C contador de ciclos (R)  <- RTL del grupo
#
# Secuencia (enunciado):
#   1. 4 LEDs encendidos >= 3 s
#   2. LED objetivo pseudoaleatorio (semilla = contador de ciclos)
#   3. medir tiempo hasta la pulsación correcta
#   4. mostrar décimas en displays (decimal, no hex)
#   5. repetir hasta 10 aciertos; luego mostrar promedio
#   6. botón incorrecto -> "EE" 0,5 s y reinicia la ronda
#      (las rondas correctas acumuladas se conservan)
#
# NOTA: la ALU no soporta shifts -> multiplicar por 2/4/16 se
# hace con sumas y las divisiones por resta repetida.
#
# Registros:
#   x1  base periféricos   x2  máscara objetivo
#   x3  botones leídos     x4  valor del display (BCD)
#   x5  scratch            x6  rondas correctas (0..10)
#   x7  suma de décimas    x8  décimas de la ronda
#   x9  t0 (ciclos)        x10 t1 / elapsed
#   x11 contador aux       x12 TENTH   x13 TRES_S   x14 10
#   x15 scratch
# =============================================================

.equ TENTH,   2500000        # ciclos por décima de segundo
.equ TRES_S,  75000000      # ciclos de la fase de espera (3 s)
.equ DIGITOS, 0              # offset displays
.equ LEDS,    4              # offset LEDs
.equ BOTONES, 8              # offset botones
.equ CICLOS,  12             # offset contador de ciclos
.equ DIEZ,    10

_start:
    lui  x1, 0x80000         # x1 = 0x8000_0000, base de periféricos
    li   x12, TENTH          # constantes de tiempo
    li   x13, TRES_S
    addi x14, x0, DIEZ       # x14 = 10
    addi x6, x0, 0           # rondas correctas = 0
    addi x7, x0, 0           # suma de décimas = 0
    sw   x0, DIGITOS(x1)     # displays en "00"
    sw   x0, LEDS(x1)        # LEDs apagados

# ----------------------- ronda actual ------------------------
ronda:
    # fase 1: los 4 LEDs encendidos durante >= 3 segundos
    addi x5, x0, 15
    sw   x5, LEDS(x1)
    lw   x9, CICLOS(x1)      # t0 de la fase de espera
espera_3s:
    lw   x10, CICLOS(x1)
    sub  x5, x10, x9         # elapsed = t1 - t0 (resta módulo 2^32)
    bltu x5, x13, espera_3s   # aún no pasan los 3 s

    # fase 2: LED objetivo pseudoaleatorio, encendido SOLO
    # semilla = contador de ciclos, mezclada con las rondas jugadas
    lw   x5, CICLOS(x1)      # semilla
    xor  x5, x5, x6          # semilla ^ rondas
    add  x10, x5, x5         # x10 = 2*semilla
    xor  x5, x5, x10         # semilla ^ 2*semilla (mezcla extra)
    andi x5, x5, 3           # 0..3
    # máscara one-hot SIN shifts: comparar/decrementar
    beqz x5, tgt0
    addi x5, x5, -1
    beqz x5, tgt1
    addi x5, x5, -1
    beqz x5, tgt2
    j    tgt3
tgt0:
    addi x2, x0, 1           # LED 0 -> 0001
    j    tgt_ok
tgt1:
    addi x2, x0, 2           # LED 1 -> 0010
    j    tgt_ok
tgt2:
    addi x2, x0, 4           # LED 2 -> 0100
    j    tgt_ok
tgt3:
    addi x2, x0, 8           # LED 3 -> 1000
tgt_ok:
    sw   x2, LEDS(x1)        # se enciende SOLO el LED objetivo
    lw   x9, CICLOS(x1)      # t0: la medición empieza con la ronda

    # fase 3: esperar la pulsación
    # (primero exigir que suelten todo: también hace de anti-rebote)
soltar:
    lw   x3, BOTONES(x1)
    bnez x3, soltar           # espera a que no haya botón apretado
presion:
    lw   x3, BOTONES(x1)
    beqz x3, presion         # nada presionado: seguir esperando
    beq  x3, x2, acierto     # botón correcto -> termina la ronda
    j    error               # cualquier otra pulsación -> error

# ----------------------- acierto ------------------------------
acierto:
    lw   x10, CICLOS(x1)     # t1
    sub  x10, x10, x9        # elapsed en ciclos
    addi x8, x0, 0           # décimas = 0
decimas:
    bltu x10, x12, dec_ok    # elapsed < 1 décima -> listo
    sub  x10, x10, x12       # elapsed -= TENTH  (división por resta)
    addi x8, x8, 1           # décimas++
    j    decimas
dec_ok:
    add  x7, x7, x8          # suma total += décimas de la ronda

    # mostrar la ronda en los displays, en DECIMAL (BCD)
    mv   x5, x8              # unidades candidatas
    addi x11, x0, 0          # decenas = 0
bcd_ronda:
    bltu x5, x14, bcd_r_fin  # x5 < 10 -> ya están las cifras
    sub  x5, x5, x14         # división por 10 por resta repetida
    addi x11, x11, 1
    j    bcd_ronda
bcd_r_fin:
    # valor = decenas*16 + unidades  (x16 sin shifter: 4 dobles)
    add  x4, x11, x11        # 2*decenas
    add  x4, x4, x4          # 4*decenas
    add  x4, x4, x4          # 8*decenas
    add  x4, x4, x4          # 16*decenas
    or   x4, x4, x5          # + unidades
    sw   x4, DIGITOS(x1)     # displays muestran "dd" en decimal

    addi x6, x6, 1           # rondas correctas++
    bne  x6, x14, ronda      # menos de 10 -> otra ronda

# --------------- fin: promedio de las 10 rondas ---------------
    mv   x5, x7              # promedio = suma / 10 por resta
    addi x11, x0, 0          # cociente
div10:
    bltu x5, x14, div_fin
    sub  x5, x5, x14
    addi x11, x11, 1
    j    div10
div_fin:
    li   x15, 5
    bltu x5, x15, sin_red    # resto < 5: no redondea
    addi x11, x11, 1        # redondeo: resto >= 5 -> +1 décima
sin_red:
    mv   x5, x11             # a BCD
    addi x11, x0, 0
bcd_prom:
    bltu x5, x14, bcd_p_fin
    sub  x5, x5, x14
    addi x11, x11, 1
    j    bcd_prom
bcd_p_fin:
    add  x4, x11, x11        # 16*decenas (4 dobles, sin shifts)
    add  x4, x4, x4
    add  x4, x4, x4
    add  x4, x4, x4
    or   x4, x4, x5
    sw   x4, DIGITOS(x1)     # displays muestran el promedio
fin:
    j    fin                 # queda mostrando el promedio

# ------------------- pulsación incorrecta ---------------------
error:
    # indicar error: displays "EE", LEDs en 0101, visible ~0,5 s
    li   x5, 0xEE
    sw   x5, DIGITOS(x1)
    addi x5, x0, 5
    sw   x5, LEDS(x1)
    lw   x9, CICLOS(x1)
    li   x15, 12500000       # 0,5 s en ciclos
err_espera:
    lw   x10, CICLOS(x1)
    sub  x5, x10, x9
    bltu x5, x15, err_espera
    j    ronda               # reinicia la ronda actual;
                             # x6 y x7 NO se tocan (acumulan)