from typing_extensions import Required
from typing import List

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
    version = '1.0'

    KEY_BYTE = [b'p']
    ACK_BYTE = b'.'

    CMD_COPY = [b'c']
    CMD_RST  = [b'r']
    CMD_EXIT = [b'x']
    
    class Baud:
        B_9600 = 9600

    allowed_input_formats = ['vhex', 'bin']

    
    class Section:
        def __init__(self, base:int, size:int, contents:List[bytes]):
            self.base = base
            self.size = size
            self.contents = contents


    def __init__(self, port:str, baud:Baud, file:str, iformat:str, base_addr:int, verbose_flag:bool=False, debug_flag:bool=False, txdelay:int=0.05):
        ## initialize atom programmer
        self._port = port
        self._baud = baud
        self._file = file
        self._iformat = iformat
        self._base_addr = base_addr
        self._ser = None
        self._verbose_flag = verbose_flag
        self._debug_flag = debug_flag
        self._txdelay = txdelay


    def __open_port(self):
        ## open serial port
        if self._ser == None:
            self._ser = serial.Serial(self._port, self._baud)


    def __close_port(self):
        ## close serial port
        if self._ser != None:
            self._ser.close()


    def __send_int(self, val:int):
        ## Send integer
        for _ in range(4):
            byte = (val & 0x000000ff).to_bytes(1, 'little')
            self._ser.write(byte)
            
            if self._debug_flag:
                print('Sent: ', hex(int.from_bytes(byte, "little")))
            
            val >>= 8
            sleep(self._txdelay)


    def __send_bytes(self, arr):
        ## Send bytes
        for b in arr:
            self._ser.write(b)
            
            if self._debug_flag:
                print('sending:',b)
            
            sleep(self._txdelay)


    def __progress(self, count, total, prefix='', suffix=''):
        ## Update program counter
        bar_len = 20
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 1)
        bar = '∎' * filled_len + ' ' * (bar_len - filled_len)

        sys.stdout.write('%s [%s] %s%s %s\r' % (prefix, bar, percents, '%', suffix))
        sys.stdout.flush()  # As suggested by Rom Ruben


    def __send_section(self, sec:Section):
        for i in range(sec.size):
            self._ser.write(sec.contents[i])
            
            if(self._debug_flag):
                print('<< ', sec.contents[i])   

            if self._verbose_flag and not self._debug_flag:
                perc = int(i*100/sec.size)
                if perc % 5 == 0:
                    self.__progress(i, sec.size)
                    pass

            sleep(self._txdelay)
        print()
        return True


    def __wait_for_ack(self)->bool:
        ## wait for acknowledgement from device
        byte = self._ser.read()
        
        if self._debug_flag:
            print('ACK recieved ', byte)

        if byte == self.ACK_BYTE:
            return True
        else:
            return False

    
    def __exit(self, reason:str):
        # exit programmer with error
        print(style.RED, '!ERROR: ', style.RESET, reason)
        sys.exit()


    def __parse_file(self) -> List[Section]:
        if self._iformat == 'bin':
            base = self._base_addr
            contents = []

            with open(self._file, "rb") as f:
                byte = f.read(1)
                while byte:
                    contents+=[byte]
                    byte = f.read(1)
                    
            return [self.Section(base, len(contents), contents)]
        
        elif self._iformat == 'vhex':
            pass


    def program(self, exit=True):
        ## program device

        # format [base_addr, size, [content]]
        sections = self.__parse_file()

        if self._verbose_flag:
            print('Port:\t', self._port)
            print('Baud:\t', self._baud, 'bps\n')

            print('File:\t', self._file)
            for i in range(len(sections)):
                print('\tSection['+str(i+1)+']\tbase: ', str.format('0x{:08X}', sections[i].base), '\tsize: ', sections[i].size, 'bytes')            
            print()

        def start_task(task:str):
            if(self._verbose_flag):
                print(style.CYAN+'>> '+task+style.RESET)
        
        def start_subtask(task:str):
            if(self._verbose_flag):
                print(style.YELLOW+'- '+task+style.RESET)

        def end_task(lines:int=1):
            if(self._verbose_flag):
                print('\033['+str(lines)+'A'+'\033[30C'+'Done!')

        def check_ack():
            if self.__wait_for_ack() == False:
                self.__exit('ACK not recieved')          


        # ----- Open serial port -----
        start_task('Initiaizing...')
        self.__open_port()
        end_task()

        # ----- send key byte -----
        start_task('Sending key byte...')
        self.__send_bytes(self.KEY_BYTE)
        check_ack()
        end_task()
        
        # ----- program sections -----
        for i in range(len(sections)):
            s = sections[i]
            start_task('Programming Section['+str(i)+']...')
            
            # send copy command
            start_subtask('Sending copy command...')
            self.__send_bytes(self.CMD_COPY)
            check_ack()
            
            # send section base address
            start_subtask('Sending section base address... ('+str.format('0x{:08X}', s.base)+')')
            self.__send_int(s.base)
            check_ack()

            # send section size
            start_subtask('Sending section size... ('+str(s.size)+' bytes)')
            self.__send_int(s.size)
            check_ack()

            # send section contents
            start_subtask('Sending section contents...')
            self.__send_section(s)
            check_ack()
            end_task()

        start_task('Sending exit command...')
        self.__send_bytes(self.CMD_EXIT)
        check_ack()
        end_task()

        # ----- Close serial port -----
        self.__close_port()

        return True


if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser()

    # Positional Arguments
    parser.add_argument("port", help="Serial port to which device is connected", type=str)
    parser.add_argument("file", help="Image file", type=str)

    # Optional Arguments
    parser.add_argument("-f", "--format", help="Input format: "+str(AtomProgrammer.allowed_input_formats), type=str, default='bin')
    parser.add_argument("-a", "--address", help="Base address (optionally required if format==bin)", type=int, default=0x00000400)
    parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
    parser.add_argument("-d", "--debug", help="Print debugging information", action="store_true")
    parser.add_argument("-b", "--baud", help="Set Uart Baudrate", type=int, default=AtomProgrammer.Baud.B_9600)

    args = parser.parse_args()


    if args.verbose:
        print(style.GREEN+'AtomProgrammer v'+AtomProgrammer.version+style.RESET)

    if args.format not in AtomProgrammer.allowed_input_formats:
        print(style.RED, 'Unsupported input format: ', style.RESET, args.format)
        sys.exit()

    # Instantiate programmer
    ap = AtomProgrammer(args.port, args.baud, args.file, args.format, args.address, args.verbose, args.debug)

    # Program
    if args.verbose and ap.program():
        print(style.YELLOW, 'Programming Successful!!', style.RESET)
