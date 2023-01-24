

import os
import re

class PR_NORMAL:
    def Red(txt, end='\n'): print("{}".format(txt),end=end)
    def Green(txt, end='\n'): print("{}".format(txt),end=end) 
    def Yellow(txt, end='\n'): print("{}".format(txt),end=end) 
    def Purple(txt, end='\n'): print("{}".format(txt),end=end) 
    def Cyan(txt, end='\n'): print("{}".format(txt),end=end) 
    def Blue(txt, end='\n'): print("{}".format(txt),end=end)
    def Reverse(txt, end='\n'): print("{}".format(txt),end=end)
    def Bold(txt, end='\n'): print("\033[1m{}\033[00m".format(txt),end=end)
     
class PR_FANCY:
    def Red(txt, end='\n'): print("\033[91m{}\033[00m".format(txt),end=end)
    def Green(txt, end='\n'): print("\033[92m{}\033[00m".format(txt),end=end) 
    def Yellow(txt, end='\n'): print("\033[93m{}\033[00m".format(txt),end=end) 
    def Purple(txt, end='\n'): print("\033[95m{}\033[00m".format(txt),end=end) 
    def Cyan(txt, end='\n'): print("\033[96m{}\033[00m".format(txt),end=end) 
    def Blue(txt, end='\n'): print("\033[94m{}\033[00m".format(txt),end=end)
    def Reverse(txt, end='\n'): print("\033[7m{}\033[00m".format(txt),end=end)
    def Bold(txt, end='\n'): print("\033[1m{}\033[00m".format(txt),end=end)


PR = PR_FANCY if int(os.getenv("HAPI_COLOUR", "1")) else PR_NORMAL

class DISPLAY:
    FORMATING = {
        'RED':'\033[91m',
        'GREEN':'\033[92m',
        'YELLOW':'\033[93m',
        'PURPLE':'\033[95m',
        'CYAN':'\033[96m',
        'BLUE':'\033[94m',
        'REVERSE':'\033[7m',
        'BOLD':'\033[1m',
        'UNDERLINE':'\033[4m',
        'TAB':'\t',
        'RESET':'\033[00m',
    }
    
    line_count = 0
    buffer = ""
    partial_line = ''

    def __init__(self):
        if int(os.getenv("HAPI_COLOUR", "0")):
            for code in self.FORMATING:
                self.FORMATING[code] = ''

    def add(self,*args):
        self.partial_line += args[0].format(*args[1:],**self.FORMATING)

    def __add_partial_line(self):
        if self.partial_line:
            self.line_count +=  1
            self.buffer += self.partial_line + '\n'
            self.partial_line = ''

    def end(self):
        self.__add_partial_line()

    def add_line(self,*args):
        self.__add_partial_line()
        self.line_count +=  1
        line = args[0].format(*args[1:],**self.FORMATING)
        self.buffer += line + '\n'

    def render(self,loop = True):
        self.__add_partial_line()
        LINE_UP = '\033[1A'
        ERASE_LINE = '\033[2K'
        print(self.buffer,end='')
        if loop:
            print((LINE_UP + ERASE_LINE) * self.line_count,end="")
            self.buffer = ''
            self.last_count = self.line_count
            self.line_count = 0

    def get_buffer(self):
        ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
        return ansi_escape.sub('',self.buffer)
