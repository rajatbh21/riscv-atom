.section .boot, "ax", @progbits
.global _start
.global _exit

_start:
    la sp, _stack_pointer       # set stack pointer

    // Jump to bootloader
    jal bootloader

    // Jump to application code
    la t0, _application
    jalr x0, 0(t0)

_exit:
    ebreak
    j _exit