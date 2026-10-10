.equ ESPERA, 75000000
    beqz x1, fin
    li x5, ESPERA
fin:
    addi x1, x0, 0