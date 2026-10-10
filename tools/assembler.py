import argparse
import re
import sys
# encoders traducen traduce a bits
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
    partes=texto.lower().split("(")
    offset= partes[0].strip()
    reg=partes[1].strip(")")
    if offset == "":
        offset = 0
    else:
        offset = int(offset, 0)

    reg = parse_reg(reg)
    return (offset, reg)

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
def calcular_offset(destino, pc, etiquetas):
    if destino not in etiquetas:
        raise ValueError(f"etiqueta no definida: {destino}")
    return etiquetas[destino] - pc
    


def ensamblar_instruccion(mnemonico, operandos, pc, etiquetas):
    if mnemonico not in TABLA:
        raise ValueError(f"instruccion desconocida: {mnemonico}")
    formato, opcode, funct3, funct7 = TABLA[mnemonico]

    if formato == "R":
        rd  = parse_reg(operandos[0])
        rs1 = parse_reg(operandos[1])
        rs2 = parse_reg(operandos[2])
        return enc_r(opcode, rd, funct3, rs1, rs2, funct7)

    if formato == "I":
        rd  = parse_reg(operandos[0])
        rs1 = parse_reg(operandos[1])
        imm = int(operandos[2], 0)
        return enc_i(opcode, rd, funct3, rs1, imm)

    if formato == "U":
        rd  = parse_reg(operandos[0])
        imm = int(operandos[1], 0)
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
        imm = calcular_offset(operandos[1], pc, etiquetas)
        return enc_j(opcode, rd, imm)

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
def primera_pasada(lineas):
    etiquetas = {}
    pc = 0
    for linea in lineas:
        etiqueta, mnemonico, operandos = analizar_linea(linea)
        if etiqueta is not None:
            etiquetas[etiqueta] = pc
        if mnemonico is None or mnemonico.startswith("."):
            continue
        pc += 4
    return etiquetas

def expandir(mnemonico, operandos):
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
       
    return [(mnemonico, operandos)]

    

#codigo para probar sw/prueba.s
def ensamblar_archivo(entrada, salida):
    with open(entrada, encoding="utf-8") as f:
        lineas = f.readlines()

    etiquetas = primera_pasada(lineas)           

    palabras = []
    pc = 0
    for linea in lineas:                       
        codigo = ensamblar_instruccion(linea, pc, etiquetas)
        if codigo is not None:
            palabras.append(codigo)
            pc += 4

    with open(salida, "w", encoding="utf-8") as f:
        for p in palabras:
            f.write(f"{p:08x}\n")

    return len(palabras)
if __name__ == "__main__":
        import sys
        if len(sys.argv) != 3:
            print("Uso: python tools/assembler.py entrada.s salida.hex")
            sys.exit(1)
        n = ensamblar_archivo(sys.argv[1], sys.argv[2])
        print(f"OK: {n} instrucciones -> {sys.argv[2]}")

