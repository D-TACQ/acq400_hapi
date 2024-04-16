#!/usr/bin/python

'''
configures PWM on UUT

'''

import epics
import time
import sys
import os

UUT=os.getenv('IOC_HOST')
SITE=os.getenv('PPW_SITE', default='4')
# we have 6 PPW but only two are physical
MAXDX=int(os.getenv('MAX_DX', default='2'))

if len(sys.argv) == 2:
    UUT = sys.argv[1]

root = f'{UUT}:{SITE}'

def pvput(suffix, value):
    name = root+suffix
    print(f'{name} {value}')
    epics.caput(name, value, wait=True)

pvput(':DIO:ENABLE', 0)
pvput(':CLKDIV',     1)
pvput(':DIO:ENABLE:clr', 1)


for dx in range(1, MAXDX):
    ppw = f':PPW:{dx}'
    pvput(ppw+":TRG",        "TRG_BUS")    
    pvput(ppw+":TRG:DX",     "d0")    
    pvput(ppw+":TRG:SENSE",  "rising")

    pvput(ppw+":REPMODE",    "CONT")

    pvput(ppw+":PULSE",      "INIT_LO")

    pvput(ppw+":PULSE:WIDTH", dx*2)
    pvput(ppw+":PULSE:DELAY", dx*2)
    pvput(ppw+":PULSE:PERIOD", dx*4)

        
pvput(':DIO:ENABLE', 1)

