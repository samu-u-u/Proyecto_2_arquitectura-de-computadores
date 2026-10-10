import argparse
import re
import sys
# encoders traducen a bits
#leer memoria 
def enc_i(opcode, rd, funct3, rs1, imm):                                             
    return((imm & 0xFFF)<< 20) | (rs1<< 15) | (funct3<< 12) | (rd << 7) | opcode
# escribir memoria
def enc_s (opcode, funct3, rs1, rs2, imm): 
    return(((imm >>5) & 0x7F)<< 25) | (rs2<< 20) | (rs1 <<15) | (funct3 << 12) | ((imm & 0x01F) << 7) | opcode
# operar dos registros
def enc_r(opcode, rd, funct3, rs1, rs2, funct7):
    return( funct7 << 25) | (rs2 <<20) | (rs1<< 15) | (funct3 << 12) | (rd<< 7) | opcode
# carghar una constante grande
def enc_u(opcode, rd, imm20):
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | opcode
# estas dos ultimas son los encoders de las instrucciones de salto.
def enc_j(opcode,rd,imm): 
    return (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20) | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | opcode
def enc_b(opcode, funct3, rs1,rs2,imm):
    return (((imm >> 12) & 1) << 31) | (((imm >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (((imm >> 1) & 0xF) << 8) | (((imm >> 11) & 1) << 7) | opcode
#validaciones 
MAX_PALABRAS = 512
PSEUDO_OPERANDOS = {"nop": 0, "mv": 2, "j": 1, "beqz": 2, "bnez": 2, "li": 2}
FORMATO_OPERANDOS = {"R": 3, "I": 3, "L": 2, "S": 2, "U": 2, "B": 3, "J": 2}


def verificar_cantidad(mnemonico, operandos, esperado):
    if len(operandos) != esperado:
        raise ValueError(f"'{mnemonico}' espera {esperado} operandos, recibio {len(operandos)}")


def parse_imm(texto, minimo, maximo):
    try:
        valor = int(texto, 0)
    except ValueError:
        raise ValueError(f"inmediato invalido: '{texto}'")
    if not (minimo <= valor <= maximo):
        raise ValueError(f"inmediato fuera de rango: {valor} (permitido {minimo} a {maximo})")
    return valor
 
# recibe el texto con comas y comentarios y lo los separa y organiza. 
REGS = {f"x{i}": i for i in range(16)}
    

TABLA = {
    "add":  ("R", 0x33, 0, 0x00),
    "sub":  ("R", 0x33, 0, 0x20),
    "xor":  ("R", 0x33, 4, 0x00),
    "or":   ("R", 0x33, 6, 0x00),
    "and":  ("R", 0x33, 7, 0x00),
    "addi": ("I", 0x13, 0, None),
    "andi": ("I", 0x13, 7, None),
    "lui":  ("U", 0x37, None, None),
    "lw": ("L", 0x03, 2, None),
    "sw": ("S", 0x23, 2, None),
    "sltu": ("R", 0x33, 3, 0x00),
    "xori": ("I", 0x13, 4, None),
    "ori":  ("I", 0x13, 6, None),

    "beq":  ("B", 0x63, 0, None),
    "bne":  ("B", 0x63, 1, None),
    "blt":  ("B", 0x63, 4, None),
    "bge":  ("B", 0x63, 5, None),
    "bltu": ("B", 0x63, 6, None),
    "bgeu": ("B", 0x63, 7, None),
    "jal":  ("J", 0x6F, None, None),
}
    

# ejemplo x5
def parse_reg(texto): 
    texto=texto.strip().lower()
    if texto in REGS: 
        return REGS[texto]
    else: 
        raise ValueError(f"registro invalido: {texto}")
# ejemplo 4(x2)
def parse_mem(texto):
    if "(" not in texto or not texto.strip().endswith(")"):
        raise ValueError(f"operando de memoria invalido: '{texto}' (use offset(registro))")
    partes = texto.lower().split("(")
    offset = partes[0].strip()
    reg = partes[1].strip(")")
    offset = 0 if offset == "" else parse_imm(offset, -2048, 2047)
    return (offset, parse_reg(reg))


def separar(linea):
    linea = linea.split("#")[0]
    linea = linea.strip()
    if linea == "":
        return None
    partes = linea.split(None, 1)
    mnemonico = partes[0].lower()
    if len(partes) == 1:
        return (mnemonico, [])
    operandos = []
    for op in partes[1].split(","):
        operandos.append(op.strip())
    return (mnemonico, operandos)

# calcula el salto 
def calcular_offset(destino, pc, etiquetas, minimo=-4096, maximo=4094):
    if destino not in etiquetas:
        raise ValueError(f"etiqueta no definida: {destino}")
    offset = etiquetas[destino] - pc
    if not (minimo <= offset <= maximo):
        raise ValueError(f"salto demasiado lejos: {offset} bytes (permitido {minimo} a {maximo})")
    return offset
    


def ensamblar_instruccion(mnemonico, operandos, pc, etiquetas):
    if mnemonico not in TABLA:
        raise ValueError(f"instruccion desconocida: {mnemonico}")
    formato, opcode, funct3, funct7 = TABLA[mnemonico]
    verificar_cantidad(mnemonico, operandos, FORMATO_OPERANDOS[formato])

    if formato == "R":
        rd  = parse_reg(operandos[0])
        rs1 = parse_reg(operandos[1])
        rs2 = parse_reg(operandos[2])
        return enc_r(opcode, rd, funct3, rs1, rs2, funct7)

    if formato == "I":
        rd  = parse_reg(operandos[0])
        rs1 = parse_reg(operandos[1])
        imm = parse_imm(operandos[2], -2048, 2047)
        return enc_i(opcode, rd, funct3, rs1, imm)

    if formato == "U":
        rd  = parse_reg(operandos[0])
        imm = parse_imm(operandos[1], 0, 0xFFFFF)
        return enc_u(opcode, rd, imm)
    
    if formato == "L": 
        rd = parse_reg(operandos[0])
        imm, rs1 = parse_mem(operandos[1])
        return enc_i(opcode, rd, funct3, rs1, imm)
    
    if formato == "S": 
        rs2=parse_reg(operandos[0])
        imm, rs1= parse_mem(operandos[1])
        return enc_s(opcode, funct3, rs1, rs2, imm)
    
    if formato == "B":                         
        rs1 = parse_reg(operandos[0])
        rs2 = parse_reg(operandos[1])
        imm = calcular_offset(operandos[2], pc, etiquetas)
        return enc_b(opcode, funct3, rs1, rs2, imm)
    
    if formato == "J":                          
        rd  = parse_reg(operandos[0])
        imm = calcular_offset(operandos[1], pc, etiquetas, -1048576, 1048574)
        return enc_j(opcode, rd, imm)
def ensamblar_linea(linea, pc=0, etiquetas={}, constantes={}):
    etiqueta, mnemonico, operandos = analizar_linea(linea)
    if mnemonico is None or mnemonico.startswith("."):
        return []
    operandos = sustituir_constantes(operandos, constantes)
    palabras = []
    for i, (m, o) in enumerate(expandir(mnemonico, operandos)):
        palabras.append(ensamblar_instruccion(m, o, pc + 4 * i, etiquetas))
    return palabras




#ejemplo usado de los botones, 
def analizar_linea(linea):
    linea = linea.split("#")[0].strip()
    etiqueta = None

    if ":" in linea:
        partes = linea.split(":", 1)
        etiqueta = partes[0].strip()
        linea = partes[1].strip()

    if linea == "":
        return (etiqueta, None, [])

    partes_d = linea.split(None, 1)
    mnemonico = partes_d[0].lower()
    if len(partes_d) == 1:
        return (etiqueta, mnemonico, [])

    operandos = [op.strip() for op in partes_d[1].split(",")]
    return (etiqueta, mnemonico, operandos)
# la idea es que esto pueda recorrer las lineas y lleva cuenta de las direcciones (empieza en 0 y suma 4 por cada instruccion real)
def primera_pasada(lineas, constantes={}):
    etiquetas = {}
    pc = 0
    for n, linea in enumerate(lineas, 1):
        etiqueta, mnemonico, operandos = analizar_linea(linea)
        if etiqueta is not None:
            if etiqueta in etiquetas:
                raise ValueError(f"linea {n}: etiqueta duplicada '{etiqueta}'")
            etiquetas[etiqueta] = pc
        if mnemonico is None or mnemonico.startswith("."):
            continue
        operandos = sustituir_constantes(operandos, constantes)
        try:
            cantidad = len(expandir(mnemonico, operandos))
        except ValueError:
            cantidad = 1          
        pc += 4 * cantidad
    return etiquetas
# las dos funciones de abajo son para, ejemplo, li x5 ESPERA pasa a ser (con expandir) li x5, 75000000

def sustituir_constantes(operandos, constantes):
    nuevos = []
    for op in operandos:
        if "(" in op:                           
            antes, resto = op.split("(", 1)
            antes = antes.strip()
            if antes in constantes:
                antes = str(constantes[antes])
            op = antes + "(" + resto
        elif op in constantes:                  
            op = str(constantes[op])
        nuevos.append(op)
    return nuevos

def leer_constantes(lineas):
    constantes = {}
    for n, linea in enumerate(lineas, 1):
        etiqueta, mnemonico, operandos = analizar_linea(linea)
        if mnemonico == ".equ":
            if len(operandos) != 2:
                raise ValueError(f"linea {n}: .equ necesita: .equ NOMBRE, valor")
            if operandos[0] in constantes:
                raise ValueError(f"linea {n}: constante duplicada '{operandos[0]}'")
            valor = sustituir_constantes([operandos[1]], constantes)[0]
            try:
                constantes[operandos[0]] = int(valor, 0)
            except ValueError:
                raise ValueError(f"linea {n}: valor invalido en .equ: '{operandos[1]}'")
    return constantes



# toma pseudoinstrucciones y las traduce a instrucciones basicas reales que el hardware de la CPU si save codificar en ceros y unos 
def expandir(mnemonico, operandos):
    if mnemonico in PSEUDO_OPERANDOS:
        verificar_cantidad(mnemonico, operandos, PSEUDO_OPERANDOS[mnemonico])    #valñidacion 
    if mnemonico == "nop":
        return [("addi", ["x0", "x0", "0"])]
    if mnemonico == "mv":
        return [("addi", [operandos[0], operandos[1], "0"])]
    if mnemonico == "j":
        return [("jal", ["x0", operandos[0]])]
    if mnemonico == "beqz":
        return [("beq", [operandos[0], "x0", operandos[1]])]
    if mnemonico == "bnez":
        return [("bne", [operandos[0], "x0", operandos[1]])]
    if mnemonico == "li":
        rd = operandos[0]
        valor = parse_imm(operandos[1], -(1 << 31), (1 << 32) - 1) & 0xFFFFFFFF #parte de validacion  
        if valor >= 0x80000000:
            valor -= 1 << 32
        if -2048 <= valor <= 2047:
            return [("addi", [rd, "x0", str(valor)])]
        bajo= valor& 0xFFF # son doce bits de abajo
        if bajo >=2048:
            bajo-=4096
        alto=((valor-bajo) >> 12) &0xFFFFF
        if bajo ==0: 
            return [("lui", [rd, str(alto)])]
        return [("lui", [rd, str(alto)]), ("addi", [rd, rd, str(bajo)])]
       
    return [(mnemonico, operandos)]

    

#codigo para probar sw/prueba.s
def ensamblar_archivo(entrada, salida):
    with open(entrada, encoding="utf-8") as f:
        lineas = f.readlines()

    constantes = leer_constantes(lineas)                 # ← se crea aquí
    etiquetas = primera_pasada(lineas, constantes)

    palabras = []
    pc = 0
    for linea in lineas:
        nuevas = ensamblar_linea(linea, pc, etiquetas, constantes)
        palabras.extend(nuevas)
        pc += 4 * len(nuevas)

    with open(salida, "w", encoding="utf-8") as f:
        for p in palabras:
            f.write(f"{p:08x}\n")

    return len(palabras)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ensamblador RV32E")
    parser.add_argument("entrada", help="archivo .s de entrada")
    parser.add_argument("salida", help="archivo .hex de salida")
    args = parser.parse_args()
    try:
        n = ensamblar_archivo(args.entrada, args.salida)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    print(f"{args.entrada} -> {args.salida} ({n} palabras)")