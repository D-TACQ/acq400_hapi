#!/usr/bin/env python3

import sys

import common
import dc
import pulse
import parabola
import cycloid_scan 

def get_wave_commands():
    return common.WAVE_CMDS

def help(unused):
    for key in sorted(get_wave_commands().keys()):
        if key not in ("help", "usage") :
            get_wave_commands()[key](('--help',))
            print()
    return None, None
            
def usage(unused):
    for key in sorted(get_wave_commands().keys()):
        if key not in ("help", "usage") :
            get_wave_commands()[key](('--usage',))
    return None, None        
            
def quit(cmd):
    if cmd == "quit":
        print("Goodbye")
        sys.exit()
    
        
common.WAVE_CMDS['help'] = help
common.WAVE_CMDS['usage'] = usage
common.WAVE_CMDS['quit'] = quit



if __name__ == "__main__":
    help(None)        



