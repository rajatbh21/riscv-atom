#include <defs.h>
#include <stdint.h>
#include <stdbool.h>

// Macros
#define BAUD 9600
#define DELAY_MS 1200
#define TIMEOUT 2000 * DELAY_MS // 2 sec

#define KEY_BYTE 'p'
#define ACK_BYTE '.'

#define CMD_COPY 'c'
#define CMD_EXIT 'x'


// sleep (time in ticks)
void sleep(unsigned int count)
{
    while(count-->0);
}


// serial read (timeout in ms)
char serial_read_timeout(unsigned int time_in_ms)
{
    char c = (char)-1;
    while(time_in_ms-- && c == (char)-1)
    {
        c = *((volatile char*) UART_D_REG_ADDR);
        sleep(DELAY_MS);
    }
    return c;
}


// serial write (uint8_t)
void serial_write(char c)
{
    while((*((volatile char*) UART_S_REG_ADDR) & 0x02) >> 1) // wait loop
        sleep(DELAY_MS);

    *((volatile char*) UART_D_REG_ADDR) = c; // send character
}


// Bootloader
void bootloader()
{   
    ////////////////// INITIALIZATION //////////////////
    // Set Baud
    *((volatile int*) UART_CD_REG_ADDR) = (CLK_FREQ/BAUD)-2;

    // clear any garbage from data register by reading it once
    *((volatile char*) UART_D_REG_ADDR);
    
    // Display splash screen
    char splash_screen [] = "Bootloader 1.0\r\n";
    for(int i=0; i<17; i++)
        serial_write(splash_screen[i]);

    //////////////////// BOOTLOADER ////////////////////
    if(serial_read_timeout(TIMEOUT) == KEY_BYTE)
    {
        // Acknowledge KEYBYTE
        serial_write(ACK_BYTE);

        // Enter Bootloader
        while(true)
        {
            // Get Command
            uint8_t cmd = serial_read_timeout(-1);

            // Acknowledge Command
            serial_write(ACK_BYTE);

            if(cmd == CMD_EXIT)  // exit
            {
                break;
            }
            else if (cmd == CMD_COPY) // copy section
            {
                // Section base address and size variables
                uint32_t base=0, size=0;

                // Get base address
                base |= (uint32_t) serial_read_timeout(-1);         // byte 0
                base |= ((uint32_t) serial_read_timeout(-1)) << 8;  // byte 1
                base |= ((uint32_t) serial_read_timeout(-1)) << 16; // byte 2
                base |= ((uint32_t) serial_read_timeout(-1)) << 24; // byte 3
                
                // Acknowledge section base address reception
                serial_write(ACK_BYTE);


                // Get size
                size |= (uint32_t) serial_read_timeout(-1);         // byte 0
                size |= ((uint32_t) serial_read_timeout(-1)) << 8;  // byte 1
                size |= ((uint32_t) serial_read_timeout(-1)) << 16; // byte 2
                size |= ((uint32_t) serial_read_timeout(-1)) << 24; // byte 3

                // Acknowledge section size reception
                serial_write(ACK_BYTE);


                // Copy loop
                for(uint32_t dptr = base; dptr<(base+size); dptr++)
                {
                    *((volatile char*) dptr) = serial_read_timeout(-1);
                }

                // Acknowledge Section Data reception
                serial_write(ACK_BYTE);
            }
        }
    }

    serial_write('B');
    return; // Boot
}