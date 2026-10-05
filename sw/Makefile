PREFIX  ?= riscv64-unknown-elf-
AS      = $(PREFIX)as
LD      = $(PREFIX)ld
OBJCOPY = $(PREFIX)objcopy

ASFLAGS = -march=rv32e -mabi=ilp32e
LDFLAGS = -m elf32lriscv -Ttext=0x0 --no-relax

SRCS  = $(wildcard *.s)
HEXS  = $(SRCS:.s=.hex)

all: $(HEXS)

%.hex: %.s
	$(AS) $(ASFLAGS) -o $*.o $<
	$(LD) $(LDFLAGS) -o $*.elf $*.o
	$(OBJCOPY) -O binary $*.elf $*.bin
	od -An -tx4 -v $*.bin | tr -s ' ' '\n' | sed '/^$$/d' > $@
	rm -f $*.o $*.elf $*.bin

clean:
	rm -f *.o *.elf *.bin *.hex

.PHONY: all clean
