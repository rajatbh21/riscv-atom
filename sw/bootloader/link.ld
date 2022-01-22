/*
    LINKER SCRIPT

    @See : https://sourceware.org/binutils/docs/ld/Basic-Script-Concepts.html
    @See : https://interrupt.memfault.com/blog/how-to-write-linker-scripts-for-firmware
    @See : https://github.com/pulp-platform/pulp-riscv-gnu-toolchain/blob/master/riscv.ld
*/

OUTPUT_ARCH("riscv")
ENTRY(_start)

/* MEMORY LAYOUT */
MEMORY
{
    BOOT    (rwx): ORIGIN = 0x00000000, LENGTH = 1K     /* 900 B */
    ROM     (rx) : ORIGIN = 0x00000400, LENGTH = 31K    /* 32 KB @ 0x0 */
    RAM     (rwx): ORIGIN = 0x04000000, LENGTH = 8K     /* 8 KB @ 0x04000000 (0.5GB boundry)*/
}

SECTIONS
{
    /* ==== ROM ==== */
    .text :
    { 
        /*  ----- Initialization Code ----- */
        *(.boot*)

        /* ----- Code ----- */
        *(.text*)

        . = ALIGN(4);        
        *(.rodata*)
        
        . = ALIGN(4);
        *(.data*)
        
        . = ALIGN(4);
    } > BOOT

    .application :
    {
        _application = .;
    } > ROM
}

PROVIDE(_stack_pointer  = ORIGIN(RAM) + LENGTH(RAM));