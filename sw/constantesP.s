.equ ESPERA, 75000000
.equ BASE, 0x80000
.equ OFFLED, 4
_start:
    lui x2, BASE
    li x5, ESPERA
    li x6, 100
loop:
    addi x5, x5, -1
    bnez x5, loop
    sw x6, OFFLED(x2)
    j _start