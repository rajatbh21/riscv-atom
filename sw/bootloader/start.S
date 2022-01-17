.section .boot, "ax", @progbits
.global _start
.global _exit

_start:
    la sp, _stack_pointer       # set stack pointer
    la gp, _global_pointer      # set global pointer
    jal bootloader

    // jump to code (absolute address 0x0000000)
    jalr x0, 0x400(x0)  
_exit:
    ebreak