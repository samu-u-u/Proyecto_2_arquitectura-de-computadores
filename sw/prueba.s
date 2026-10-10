# enciende los 4 LEDs
lui  x2, 0x80000     # base de perifericos
addi x1, x0, 15
sw   x1, 4(x2)

lw   x3, 8(x2)       # lee botones
sw   x3, 4(x2)

