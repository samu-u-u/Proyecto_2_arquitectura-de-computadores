from assembler import *

# ---------- encoders ----------
print(f"{enc_r(0x33, 5, 0, 3, 4, 0x20):08x}")    # 404182b3
print(f"{enc_u(0x37, 2, 0x80000):08x}")          # 80000137
print(f"{enc_s(0x23, 2, 2, 1, 0):08x}")          # 00112023
print(f"{enc_i(0x13, 1, 0, 0, 1):08x}")          # 00100093
print(f"{enc_i(0x13, 3, 0, 3, -1):08x}")         # fff18193
print(f"{enc_s(0x23, 2, 2, 1, -4):08x}")         # fe112e23

# ---------- funciones auxiliares ----------
print(parse_reg("x5"))                           # 5
print(separar("addi x1, x0, 1   # comentario"))  # ('addi', ['x1', 'x0', '1'])
print(separar("lw x1, 0(x2)"))                   # ('lw', ['x1', '0(x2)'])
print(separar("   # solo comentario"))           # None
print(parse_mem("4(x2)"))                        # (4, 2)

# ---------- instrucciones completas ----------
# print(f"{ensamblar_linea('add x3, x1, x2'):08x}")        # 002081b3
# print(f"{ensamblar_linea('sub x5, x3, x4'):08x}")        # 404182b3
# print(f"{ensamblar_linea('and x3, x1, x2'):08x}")        # 0020f1b3
# print(f"{ensamblar_linea('or x3, x1, x2'):08x}")         # 0020e1b3
# print(f"{ensamblar_linea('xor x3, x1, x2'):08x}")        # 0020c1b3
# print(f"{ensamblar_linea('addi x1, x0, 1'):08x}")        # 00100093
# print(f"{ensamblar_linea('addi x3, x3, -1'):08x}")       # fff18193
# print(f"{ensamblar_linea('addi x1, x0, 0x10'):08x}")     # 01000093
# print(f"{ensamblar_linea('andi x4, x1, 15'):08x}")       # 00f0f213
# print(f"{ensamblar_linea('lui x2, 0x80000'):08x}")       # 80000137
# print(f"{ensamblar_linea('lui x3, 0x12345'):08x}")       # 123451b7
# print(f"{ensamblar_linea('sub x15, x15, x15'):08x}")     # 40f787b3
# print(f"{ensamblar_linea('lw x1, 0(x2)'):08x}")          # 00012083
# print(f"{ensamblar_linea('lw x1, 8(x2)'):08x}")          # 00812083
# print(f"{ensamblar_linea('sw x1, 0(x2)'):08x}")          # 00112023
# print(f"{ensamblar_linea('sw x1, -4(x2)'):08x}")         # fe112e23

# # ---------- formato del texto ----------
# print(f"{ensamblar_linea('ADDI X1 , X0 ,   1   # may y espacios'):08x}")  # 00100093
# print(ensamblar_linea('# solo comentario'))      # None
# print(ensamblar_linea(''))                       # None

# ---------- errores (se atrapan para que no detengan el programa) ----------
# for caso in ['mul x1, x2, x3', 'addi x16, x0, 1']:
#     try:
#         ensamblar_linea(caso)
#         print(f"{caso!r} -> NO dio error (revisar)")
#     except ValueError as e:
#         print(f"{caso!r} -> ValueError: {e}")

print(REGS)

print(f"{analizar_linea("loop:")}")
print(f"{analizar_linea("loop: addi x1, x0, 1")}")
print(f"{analizar_linea("addi x1, x0, 1  # c")}")
print(f"{analizar_linea("# solo comentario")}")
print(f"{analizar_linea(" jal  x0, loop")}")

for nombre in ["buttons_leds", "blink", "7seg"]:
    with open(f"sw/{nombre}.s", encoding="utf-8") as f:
        print(nombre, primera_pasada(f.readlines()))

# print(ensamblar_linea('.section .text'))          # None
# print(ensamblar_linea('_start:'))                 # None
# print(f"{ensamblar_linea('loop: addi x1, x0, 1'):08x}")   # 00100093

print(expandir("nop", []))                    # [('addi', ['x0', 'x0', '0'])]
print(expandir("mv", ["x7", "x9"]))           # [('addi', ['x7', 'x9', '0'])]
print(expandir("j", ["fin"]))                 # [('jal', ['x0', 'fin'])]
print(expandir("beqz", ["x3", "fin"]))        # [('beq', ['x3', 'x0', 'fin'])]
print(expandir("bnez", ["x3", "fin"]))        # [('bne', ['x3', 'x0', 'fin'])]
print(expandir("add", ["x1", "x2", "x3"]))    # [('add', ['x1', 'x2', 'x3'])]