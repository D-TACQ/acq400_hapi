#!/usr/bin/env python3

import os
import re

class PR_NORMAL:
    def Red(txt, end='\n'): print("{}".format(txt), end=end)
    def Green(txt, end='\n'): print("{}".format(txt), end=end) 
    def Yellow(txt, end='\n'): print("{}".format(txt), end=end) 
    def Purple(txt, end='\n'): print("{}".format(txt), end=end) 
    def Cyan(txt, end='\n'): print("{}".format(txt), end=end) 
    def Blue(txt, end='\n'): print("{}".format(txt), end=end)
    def Reverse(txt, end='\n'): print("{}".format(txt), end=end)
    def Bold(txt, end='\n'): print("\033[1m{}\033[00m".format(txt), end=end)
     
class PR_FANCY:
    def Red(txt, end='\n'): print("\033[91m{}\033[00m".format(txt), end=end)
    def Green(txt, end='\n'): print("\033[92m{}\033[00m".format(txt), end=end) 
    def Yellow(txt, end='\n'): print("\033[93m{}\033[00m".format(txt), end=end) 
    def Purple(txt, end='\n'): print("\033[95m{}\033[00m".format(txt), end=end) 
    def Cyan(txt, end='\n'): print("\033[96m{}\033[00m".format(txt), end=end) 
    def Blue(txt, end='\n'): print("\033[94m{}\033[00m".format(txt), end=end)
    def Reverse(txt, end='\n'): print("\033[7m{}\033[00m".format(txt), end=end)
    def Bold(txt, end='\n'): print("\033[1m{}\033[00m".format(txt), end=end)


PR = PR_FANCY if int(os.getenv("HAPI_COLOUR", "1")) else PR_NORMAL

class DISPLAY:
    FORMAT_CODES = {
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
            for code in self.FORMAT_CODES:
                self.FORMAT_CODES[code] = ''

    def add(self, *args):
        self.partial_line += args[0].format(*args[1:], **self.FORMAT_CODES)

    def __add_partial_line(self):
        if self.partial_line:
            self.line_count +=  1
            self.buffer += self.partial_line + '\n'
            self.partial_line = ''

    def end(self):
        self.__add_partial_line()

    def add_line(self, *args):
        self.__add_partial_line()
        self.line_count +=  1
        line = args[0].format(*args[1:], **self.FORMAT_CODES)
        self.buffer += line + '\n'

    def render(self, loop = True):
        self.__add_partial_line()
        LINE_UP = '\033[1A'
        ERASE_LINE = '\033[2K'
        print(self.buffer,end='')
        if loop:
            print((LINE_UP + ERASE_LINE) * self.line_count, end="")
            self.buffer = ''
            self.last_count = self.line_count
            self.line_count = 0

    def get_buffer(self):
        ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
        return ansi_escape.sub('', self.buffer)

def unit_test():
    import time
    count1 = 0
    count2 = 0
    max = 100

    SCREEN = DISPLAY()

    while True:
        SCREEN.add_line("Count 1 is {0}", count1)

        SCREEN.add("Count 1 is ")
        if count1 % 5 == 0 and count1 % 3 == 0:
            SCREEN.add("divisible by 5 {UNDERLINE}and{RESET} 3")
        elif count1 % 5 == 0:
            SCREEN.add("divisible by 5")
        elif count1 % 3 == 0:
            SCREEN.add("divisible by 3")
        else:
            SCREEN.add("divisible by neither 5 or 3")
        
        SCREEN.end()
        SCREEN.add("{0:.1f} seconds since epoch", time.time())
        SCREEN.add_line("Count 2 is {BOLD}{0}{RESET} and is {1} from {2}", count2,max - count2,max)  

        if count2 > 100:
            SCREEN.render(False)
            break

        SCREEN.render()
        time.sleep(1)
        count1 += 1
        count2 += 3


    print("printing normally")
    PR.Green("Green if env set")

if __name__ == '__main__':
    unit_test()
