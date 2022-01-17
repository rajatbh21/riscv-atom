
CC = riscv64-unknown-elf-gcc
CFLAGS = -mabi=ilp32 -march=rv32i -nostdlib -nostartfiles -ffreestanding -I ${RVATOM_LIB}/include -T link.ld -DTARGET_HYDROGENSOC
LFLAGS = -Wl,--gc-sections,--print-memory-usage,--Map=bootloader_map

executble = bootloader.elf

$(executble): start.S bootloader.c
	$(CC) $(CFLAGS) $^ -o $@ $(LFLAGS)
	riscv64-unknown-elf-objdump -htd $(executble) > objdump

clean:
	rm -f $(executble)

.PHONY: genport
genport:
	atomsim-gen-vports
