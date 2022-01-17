from typing_extensions import Required
import serial
import os
import sys
from time import sleep

class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


class AtomProgrammer:
    KEY_BYTE = [b'p']
    ACK_BYTE = b'.'
    
    BaseAddr = 0x000000400  # start of ROM

    class Baud:
        B_9600 = 9600

    def __init__(self, port:str, baud:Baud, file:str, verbose_flag:bool=False, debug_flag:bool=False, txdelay:int=0.07):
        ## initialize atom programmer
        self._port = port
        self._baud = baud
        self._file = file
        self._ser = None
        self._verbose_flag = verbose_flag
        self._debug_flag = debug_flag
        self._txdelay = txdelay


    def _open_port(self):
        ## open serial port
        if self._ser == None:
            self._ser = serial.Serial(self._port, self._baud)


    def _close_port(self):
        ## close serial port
        if self._ser != None:
            self._ser.close()


    def _send_int(self, val:int):
        ## Send integer
        for _ in range(4):
            byte = (val & 0x000000ff).to_bytes(1, 'little')
            self._ser.write(byte)
            
            if self._debug_flag:
                print('Sent: ', hex(int.from_bytes(byte, "little")))
            
            val >>= 8
            sleep(self._txdelay)


    def _send_bytes(self, arr):
        ## Send bytes
        for b in arr:
            self._ser.write(b)
            
            if self._debug_flag:
                print('sending:',b)
            
            sleep(self._txdelay)


    def _progress(self, count, total, prefix='', suffix=''):
        ## Update program counter
        bar_len = 20
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 1)
        bar = '∎' * filled_len + ' ' * (bar_len - filled_len)

        sys.stdout.write('%s [%s] %s%s %s\r' % (prefix, bar, percents, '%', suffix))
        sys.stdout.flush()  # As suggested by Rom Ruben


    def _send_fcontents(self, file:str, sz:int):
        ## Send contentes of file
        with open(file, "rb") as f:
            for i in range(sz):
                byte = f.read(1)
                self._ser.write(byte)
                
                if self._verbose_flag:
                    perc = int(i*100/sz)
                    if perc % 5 == 0:
                        self._progress(i, sz, style.GREEN + 'Programming...        ' + style.RESET)

                sleep(self._txdelay)
        
        if self._verbose_flag:
            print('\t\tDone!')


    def _wait_for_ack(self, timeout=2):
        ## wait for acknowledgement from device
        byte = self._ser.read()
        
        if self._debug_flag:
            print('ACK recieved ', byte)

        if byte == self.ACK_BYTE:
            return True
        else:
            return False

    
    def _exit(self, reason:str):
        # exit programmer with error
        print(style.RED, '!ERROR: ', style.RESET, reason)
        sys.exit()


    def program(self, base:int, exit=True):
        ## program device
        fsize = os.path.getsize(self._file)

        if self._verbose_flag:
            print('Port: ', self._port)
            print('Baud: ', self._baud, 'bps\n')

            print('File: ', self._file)
            print('Base: ', hex(base))
            print('Size: ', fsize, 'bytes\n')
            

        if(self._verbose_flag):
            print(style.GREEN+'Initializing...'+style.RESET, end='')

        # ----- Open serial port -----
        self._open_port()

        if self._verbose_flag:
            print('  Done!')
        

        # ----- send key byte -----
        if(self._verbose_flag):
            print(style.GREEN+'Sending key byte...'+style.RESET, end='')
        
        self._send_bytes(self.KEY_BYTE)
        if not self._wait_for_ack():
            self._exit('ACK not recieved')
        
        if self._verbose_flag:
            print('  Done!')

        
        # ----- send command -----
        if(self._verbose_flag):
            print(style.GREEN+'Sending copy command...'+style.RESET, end='')

        self._send_bytes([b'c'])
        if not self._wait_for_ack():
            self._exit('ACK not recieved')
        
        if self._verbose_flag:
            print('  Done!')
        
        
        # ----- Send base address -----
        if(self._verbose_flag):
            print(style.GREEN+'Sending base address...'+style.RESET, end='')

        self._send_int(base)
        if not self._wait_for_ack():
            self._exit('ACK not recieved')

        if self._verbose_flag:
            print('  Done!')


        # ----- Send file size -----
        if(self._verbose_flag):
            print(style.GREEN+'Sent file size...'+style.RESET, end='')

        self._send_int(fsize)
        if not self._wait_for_ack():
            self._exit('ACK not recieved')

        if self._verbose_flag:
            print('  Done!')
       

        # ----- send file contents -----

        self._send_fcontents(self._file, fsize)
        if not self._wait_for_ack():
            self._exit('ACK not recieved')


        # ----- exit programming mode -----
        if exit:
            
            if(self._verbose_flag):
                print(style.GREEN+'Sending exit command...'+style.RESET, end='')

            self._ser.write(b'x')
            if not self._wait_for_ack():
                self._exit('ACK not recieved')

            if self._verbose_flag:
                print('\tDone!')

        # ----- Close serial port -----
        self._close_port()

        return True



if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser()

    # Positional Arguments
    parser.add_argument("port", help="Serial port to which device is connected", type=str)
    parser.add_argument("file", help="Binary image file", type=str)

    # Optional Arguments
    parser.add_argument("-a", "--address", help="Base address", type=int, default=AtomProgrammer.BaseAddr)
    parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
    parser.add_argument("-d", "--debug", help="Print debugging information", action="store_true")
    parser.add_argument("-b", "--baud", help="Set Uart Baudrate", type=int, default=AtomProgrammer.Baud.B_9600)

    args = parser.parse_args()

    ap = AtomProgrammer(args.port, args.baud, args.file, args.verbose, args.debug)

    if ap.program(args.address):
        print(style.YELLOW, 'Programming Successful!!', style.RESET)
