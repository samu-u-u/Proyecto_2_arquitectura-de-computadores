# Custom assembler for RV32E
# Uses the project's own assembler (tools/assembler.py) instead of external RISC-V toolchain
.SUFFIXES:

PYTHON ?= python3
ASSEMBLER = $(PYTHON) ../tools/assembler.py

SRCS  = $(wildcard *.s)
HEXS  = $(SRCS:.s=.hex)

all: $(HEXS)

%.hex: %.s
	$(ASSEMBLER) $< $@

clean:
	rm -f *.o *.elf *.bin *.hex

.PHONY: all clean

# Keep old rules for backward compatibility (requires RISC-V toolchain)
# To use the external RISC-V toolchain instead, uncomment these lines:
# PREFIX  ?= riscv64-unknown-elf-
# AS      = $(PREFIX)as
# LD      = $(PREFIX)ld
# OBJCOPY = $(PREFIX)objcopy
# ASFLAGS = -march=rv32e -mabi=ilp32e
# LDFLAGS = -m elf32lriscv -Ttext=0x0 --no-relax
