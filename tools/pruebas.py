"""
pruebas.py - Pruebas del assembler.

Ejecutar desde cualquier carpeta:
    python tools\\pruebas.py

Cada prueba imprime OK o FALLA. Al final muestra cuantas pasaron.
"""
import os
import tempfile

from assembler import *

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pasadas = 0
total = 0


# ---------------------------------------------------------------------------
# Utilidades de las pruebas
# ---------------------------------------------------------------------------
def hex8(n):
    return f"{n:08x}"


def una_palabra(linea, pc=0, etiquetas={}):
    """Ensambla una linea que genera una sola palabra (o None si no genera)."""
    palabras = ensamblar_linea(linea, pc, etiquetas)
    return palabras[0] if palabras else None


def verificar(nombre, obtenido, esperado):
    global pasadas, total
    total += 1
    if obtenido == esperado:
        pasadas += 1
        print(f"  OK     {nombre}")
    else:
        print(f"  FALLA  {nombre}: obtuvo {obtenido!r}, esperaba {esperado!r}")


def verificar_error(nombre, funcion, fragmento):
    """Comprueba que la funcion lance un error cuyo mensaje contenga 'fragmento'."""
    global pasadas, total
    total += 1
    try:
        funcion()
    except Exception as e:
        if fragmento in str(e):
            pasadas += 1
            print(f"  OK     {nombre}  ->  {type(e).__name__}: {e}")
        else:
            print(f"  FALLA  {nombre}: el error fue '{e}', esperaba que dijera '{fragmento}'")
    else:
        print(f"  FALLA  {nombre}: NO dio error")


def seccion(titulo):
    print(f"\n--- {titulo} ---")


def leer_hex(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read().split()


# ---------------------------------------------------------------------------
seccion("Encoders")
verificar("enc_r  sub x5, x3, x4",     hex8(enc_r(0x33, 5, 0, 3, 4, 0x20)), "404182b3")
verificar("enc_u  lui x2, 0x80000",    hex8(enc_u(0x37, 2, 0x80000)),       "80000137")
verificar("enc_s  sw x1, 0(x2)",       hex8(enc_s(0x23, 2, 2, 1, 0)),       "00112023")
verificar("enc_s  sw x1, -4(x2)",      hex8(enc_s(0x23, 2, 2, 1, -4)),      "fe112e23")
verificar("enc_i  addi x1, x0, 1",     hex8(enc_i(0x13, 1, 0, 0, 1)),       "00100093")
verificar("enc_i  addi x3, x3, -1",    hex8(enc_i(0x13, 3, 0, 3, -1)),      "fff18193")
verificar("enc_j  jal x0, -8",         hex8(enc_j(0x6F, 0, -8)),            "ff9ff06f")
verificar("enc_j  jal x0, -20",        hex8(enc_j(0x6F, 0, -20)),           "fedff06f")
verificar("enc_j  jal x1, +8",         hex8(enc_j(0x6F, 1, 8)),             "008000ef")
verificar("enc_b  bne x3, x0, -4",     hex8(enc_b(0x63, 1, 3, 0, -4)),      "fe019ee3")
verificar("enc_b  beq x1, x2, +8",     hex8(enc_b(0x63, 0, 1, 2, 8)),       "00208463")
verificar("enc_b  bne x4, x5, +8",     hex8(enc_b(0x63, 1, 4, 5, 8)),       "00521463")
verificar("enc_b  bne x1, x5, -40",    hex8(enc_b(0x63, 1, 1, 5, -40)),     "fc509ce3")

# ---------------------------------------------------------------------------
seccion("Funciones auxiliares")
verificar("parse_reg x5",              parse_reg("x5"),   5)
verificar("parse_reg x15",             parse_reg("x15"),  15)
verificar("parse_reg X7 (mayuscula)",  parse_reg("X7"),   7)
verificar("parse_mem 4(x2)",           parse_mem("4(x2)"),   (4, 2))
verificar("parse_mem -4(x2)",          parse_mem("-4(x2)"),  (-4, 2))
verificar("parse_mem (x2) sin offset", parse_mem("(x2)"),    (0, 2))
verificar("parse_mem 0x10(x5)",        parse_mem("0x10(x5)"), (16, 5))

verificar("analizar: instruccion",
          analizar_linea("addi x1, x0, 1   # comentario"),
          (None, "addi", ["x1", "x0", "1"]))
verificar("analizar: lw con memoria",
          analizar_linea("lw x1, 0(x2)"),
          (None, "lw", ["x1", "0(x2)"]))
verificar("analizar: etiqueta sola",
          analizar_linea("loop:"),
          ("loop", None, []))
verificar("analizar: etiqueta e instruccion",
          analizar_linea("loop: addi x1, x0, 1"),
          ("loop", "addi", ["x1", "x0", "1"]))
verificar("analizar: solo comentario",
          analizar_linea("   # solo comentario"),
          (None, None, []))
verificar("analizar: linea vacia",
          analizar_linea(""),
          (None, None, []))
verificar("analizar: sin operandos",
          analizar_linea("nop"),
          (None, "nop", []))

# ---------------------------------------------------------------------------
seccion("Instrucciones completas")
casos = [
    ("add x3, x1, x2",         "002081b3"),
    ("sub x5, x3, x4",         "404182b3"),
    ("and x3, x1, x2",         "0020f1b3"),
    ("or x3, x1, x2",          "0020e1b3"),
    ("xor x3, x1, x2",         "0020c1b3"),
    ("addi x1, x0, 1",         "00100093"),
    ("addi x3, x3, -1",        "fff18193"),
    ("addi x1, x0, 0x10",      "01000093"),
    ("andi x4, x1, 15",        "00f0f213"),
    ("lui x2, 0x80000",        "80000137"),
    ("lui x3, 0x12345",        "123451b7"),
    ("sub x15, x15, x15",      "40f787b3"),
    ("lw x1, 0(x2)",           "00012083"),
    ("lw x1, 8(x2)",           "00812083"),
    ("sw x1, 0(x2)",           "00112023"),
    ("sw x1, -4(x2)",          "fe112e23"),
    ("ADDI X1 , X0 ,   1   # mayusculas y espacios", "00100093"),
    ("loop: addi x1, x0, 1",   "00100093"),
]
for texto, esperado in casos:
    verificar(texto, hex8(una_palabra(texto)), esperado)

verificar("comentario solo -> sin codigo",   ensamblar_linea("# solo comentario"), [])
verificar("linea vacia -> sin codigo",       ensamblar_linea(""),                  [])
verificar("etiqueta sola -> sin codigo",     ensamblar_linea("_start:"),           [])
verificar("directiva -> sin codigo",         ensamblar_linea(".section .text"),    [])

# ---------------------------------------------------------------------------
seccion("Saltos con etiquetas")
et = {"loop": 4, "fin": 24}
verificar("bne x1, x0, loop  (pc=8, hacia atras)",
          hex8(una_palabra("bne x1, x0, loop", 8, et)), "fe009ee3")
verificar("jal x0, fin  (pc=16, hacia adelante)",
          hex8(una_palabra("jal x0, fin", 16, et)), "0080006f")

# ---------------------------------------------------------------------------
seccion("Tabla de etiquetas (primera pasada)")
for nombre, esperado in [
    ("buttons_leds", {"_start": 0, "loop": 16}),
    ("blink",        {"_start": 0, "loop": 12, "delay": 20}),
    ("7seg",         {"_start": 0, "loop": 8, "delay": 16, "skip": 44}),
]:
    ruta = os.path.join(RAIZ, "sw", f"{nombre}.s")
    with open(ruta, encoding="utf-8") as f:
        verificar(f"etiquetas de {nombre}.s", primera_pasada(f.readlines()), esperado)

# ---------------------------------------------------------------------------
seccion("Pseudoinstrucciones: expandir")
verificar("nop",         expandir("nop", []),                [("addi", ["x0", "x0", "0"])])
verificar("mv x7, x9",   expandir("mv", ["x7", "x9"]),       [("addi", ["x7", "x9", "0"])])
verificar("j fin",       expandir("j", ["fin"]),             [("jal", ["x0", "fin"])])
verificar("beqz x3, fin", expandir("beqz", ["x3", "fin"]),   [("beq", ["x3", "x0", "fin"])])
verificar("bnez x3, fin", expandir("bnez", ["x3", "fin"]),   [("bne", ["x3", "x0", "fin"])])
verificar("add (sin cambios)",
          expandir("add", ["x1", "x2", "x3"]),               [("add", ["x1", "x2", "x3"])])

seccion("Pseudoinstrucciones: programa completo")
programa = [
    "_start:",
    "    nop",
    "    mv   x1, x2",
    "    beqz x3, fin",
    "loop:",
    "    bnez x3, loop",
    "    j    fin",
    "    addi x4, x0, 1",
    "fin:",
    "    addi x5, x0, 2",
]
etiquetas = primera_pasada(programa)
verificar("etiquetas del programa", etiquetas, {"_start": 0, "loop": 12, "fin": 24})
palabras = []
pc = 0
for linea in programa:
    nuevas = ensamblar_linea(linea, pc, etiquetas)
    palabras.extend(nuevas)
    pc += 4 * len(nuevas)
verificar("codigo del programa",
          [hex8(p) for p in palabras],
          ["00000013", "00010093", "00018863", "00019063",
           "0080006f", "00100213", "00200293"])

# ---------------------------------------------------------------------------
seccion("Programas oficiales del repo (deben salir identicos)")
with tempfile.TemporaryDirectory() as tmp:
    for nombre in ["buttons_leds", "blink", "7seg"]:
        entrada = os.path.join(RAIZ, "sw", f"{nombre}.s")
        oficial = os.path.join(RAIZ, "sw", f"{nombre}.hex")
        salida = os.path.join(tmp, f"{nombre}.hex")
        ensamblar_archivo(entrada, salida)
        verificar(f"{nombre}.hex", leer_hex(salida), leer_hex(oficial))

# ---------------------------------------------------------------------------
seccion("Pseudoinstruccion li")
verificar("li x5, 100 (una instruccion)",
          expandir("li", ["x5", "100"]), [("addi", ["x5", "x0", "100"])])
verificar("li x5, 2500000",
          expandir("li", ["x5", "2500000"]),
          [("lui", ["x5", "610"]), ("addi", ["x5", "x5", "1440"])])
verificar("li x5, 75000000 (parte baja negativa)",
          expandir("li", ["x5", "75000000"]),
          [("lui", ["x5", "18311"]), ("addi", ["x5", "x5", "-1856"])])
verificar("li x5, 4096 (solo lui)",
          expandir("li", ["x5", "4096"]), [("lui", ["x5", "1"])])
verificar("li x5, 2048",
          expandir("li", ["x5", "2048"]),
          [("lui", ["x5", "1"]), ("addi", ["x5", "x5", "-2048"])])
verificar("li x5, -1",
          expandir("li", ["x5", "-1"]), [("addi", ["x5", "x0", "-1"])])
verificar("li x5, 0xFFFFFFFF  (es -1 en 32 bits)",
          expandir("li", ["x5", "0xFFFFFFFF"]), [("addi", ["x5", "x0", "-1"])])
verificar("li x5, 100 -> codigo",
          [hex8(w) for w in ensamblar_linea("li x5, 100")], ["06400293"])
verificar("li x5, 2500000 -> codigo",
          [hex8(w) for w in ensamblar_linea("li x5, 2500000")], ["002622b7", "5a028293"])
verificar("li x5, 75000000 -> codigo",
          [hex8(w) for w in ensamblar_linea("li x5, 75000000")], ["047872b7", "8c028293"])

# ---------------------------------------------------------------------------
seccion("Constantes .equ")
verificar("sustituir: registro y numero no cambian",
          sustituir_constantes(["x1", "5"], {"N": 7}), ["x1", "5"])
verificar("sustituir: nombre simple",
          sustituir_constantes(["x1", "N"], {"N": 7}), ["x1", "7"])
verificar("sustituir: offset en memoria",
          sustituir_constantes(["x1", "OFF(x2)"], {"OFF": 4}), ["x1", "4(x2)"])
verificar("leer_constantes",
          leer_constantes([".equ A, 10", ".equ B, 0x20", "nop"]), {"A": 10, "B": 32})
verificar("leer_constantes usando una anterior",
          leer_constantes([".equ A, 10", ".equ B, A"]), {"A": 10, "B": 10})
verificar("li con constante",
          [hex8(w) for w in ensamblar_linea("li x5, ESPERA", 0, {}, {"ESPERA": 75000000})],
          ["047872b7", "8c028293"])
verificar("sw con offset constante",
          hex8(ensamblar_linea("sw x6, OFFLED(x2)", 0, {}, {"OFFLED": 4})[0]), "00612223")

def ensamblar_texto(texto):
    """Escribe 'texto' en un .s temporal, lo ensambla y devuelve (palabras_hex, mensaje_error)."""
    with tempfile.TemporaryDirectory() as tmp:
        entrada = os.path.join(tmp, "t.s")
        salida = os.path.join(tmp, "t.hex")
        with open(entrada, "w", encoding="utf-8") as f:
            f.write(texto)
        try:
            ensamblar_archivo(entrada, salida)
        except ValueError as e:
            return None, str(e)
        return leer_hex(salida), None

seccion("Archivos completos con constantes y li")
codigo, _ = ensamblar_texto(""".equ ESPERA, 75000000
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
""")
verificar("programa con .equ y li",
          codigo,
          ["80000137", "047872b7", "8c028293", "06400313",
           "fff28293", "fe029ee3", "00612223", "fe5ff06f"])

codigo, _ = ensamblar_texto(""".equ ESPERA, 75000000
    beqz x1, fin
    li x5, ESPERA
fin:
    addi x1, x0, 0
""")
verificar("etiqueta despues de un li de dos palabras (salto +12)",
          codigo, ["00008663", "047872b7", "8c028293", "00000093"])

codigo_a, _ = ensamblar_texto(".equ T, 75000000\n    li x5, T\n")
codigo_b, _ = ensamblar_texto(".equ T, 50000000\n    li x5, T\n")
verificar("cambiar una constante cambia el hex", codigo_a != codigo_b, True)

# ---------------------------------------------------------------------------
seccion("Errores que deben detectarse")
verificar_error("instruccion desconocida",
                lambda: ensamblar_linea("mul x1, x2, x3"), "instruccion desconocida")
verificar_error("registro x16 (solo existen x0-x15)",
                lambda: ensamblar_linea("addi x16, x0, 1"), "registro invalido")
verificar_error("registro con nombre invalido",
                lambda: ensamblar_linea("addi foo, x0, 1"), "registro invalido")
verificar_error("etiqueta no definida",
                lambda: ensamblar_linea("jal x0, nada", 0, {}), "etiqueta no definida")
verificar_error("faltan operandos",
                lambda: ensamblar_linea("add x1, x2"), "espera 3 operandos")
verificar_error("sobran operandos",
                lambda: ensamblar_linea("addi x1, x0, 1, 2"), "espera 3 operandos")
verificar_error("pseudoinstruccion sin operandos",
                lambda: ensamblar_linea("li x3"), "espera 2 operandos")
verificar_error("inmediato demasiado grande",
                lambda: ensamblar_linea("addi x1, x0, 2048"), "fuera de rango")
verificar_error("inmediato demasiado negativo",
                lambda: ensamblar_linea("addi x1, x0, -2049"), "fuera de rango")
verificar_error("inmediato que no es numero",
                lambda: ensamblar_linea("addi x1, x0, hola"), "inmediato invalido")
verificar_error("lui fuera de rango",
                lambda: ensamblar_linea("lui x1, 0x100000"), "fuera de rango")
verificar_error("offset de memoria fuera de rango",
                lambda: ensamblar_linea("lw x1, 5000(x2)"), "fuera de rango")
verificar_error("operando de memoria sin parentesis",
                lambda: ensamblar_linea("lw x1, 4"), "operando de memoria invalido")
verificar_error("salto demasiado lejos",
                lambda: ensamblar_linea("beq x0, x0, fin", 0, {"fin": 10000}), "salto demasiado lejos")

seccion("Errores en archivos completos (con numero de linea)")
_, msg = ensamblar_texto("nop\nnop\naddi x1, x0, 9999\n")
verificar("error apunta a la linea 3", msg is not None and "linea 3" in msg, True)

_, msg = ensamblar_texto("addi x1, x0, 5000\nmul x1, x2, x3\nj nada\n")
verificar("se informan todos los errores a la vez",
          msg is not None and "linea 1" in msg and "linea 2" in msg and "linea 3" in msg, True)

_, msg = ensamblar_texto("loop:\n    nop\nloop:\n    nop\n")
verificar("etiqueta duplicada (linea 3)",
          msg is not None and "etiqueta duplicada" in msg and "linea 3" in msg, True)

_, msg = ensamblar_texto(".equ A, 1\n.equ A, 2\n")
verificar("constante duplicada",
          msg is not None and "constante duplicada" in msg, True)

_, msg = ensamblar_texto(".equ A, zzz\n")
verificar("valor invalido en .equ",
          msg is not None and "valor invalido" in msg, True)

_, msg = ensamblar_texto("nop\n" * 600)
verificar("programa mas grande que la RAM (512 palabras)",
          msg is not None and "512" in msg, True)

_, msg = ensamblar_texto("beq x0, x0, fin\n" + "nop\n" * 1100 + "fin: nop\n")
verificar("salto fuera de alcance en un archivo",
          msg is not None and "salto demasiado lejos" in msg, True)

codigo, msg = ensamblar_texto("_start:\n    nop\n    li x5, 75000000\n")
verificar("un archivo correcto no da error", msg, None)

# ---------------------------------------------------------------------------
print(f"\n=== {pasadas} de {total} pruebas pasaron ===")
if pasadas != total:
    print("Hay pruebas que fallan: revisa las lineas marcadas como FALLA.")