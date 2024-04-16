#!/usr/bin/python

'''
configures PWM on UUT

'''

import epics
import time
import sys
import os

UUT=os.getenv('IOC_HOST')
SITE=4

if len(sys.argv) == 2:
    UUT = sys.argv[1]

#acq2106_355:5:PPW:1:TRG :DX :SENSE
#acq2106_355:5:PPW:1:PULSE:ICOUNT OCOUNT GP REPS
#acq2106_355:5:PPW:1:PULSE

root = "{}:{}:PPW".format(UUT, SITE)

def pvput(suffix, value):
    name = root+suffix
    print("{} {}".format(name, value))
    epics.caput(name, value, wait=True)

dioen = "{}:{}:DIO:ENABLE".format(UUT, SITE)
clkdiv = "{}:{}:CLKDIV".format(UUT, SITE)
countclr = "{}:{}:DIO:ENABLE:clr".format(UUT, SITE)

epics.caput(dioen, 0, wait=True)

epics.caput(clkdiv, 1, wait=True)
epics.caput(countclr, 1, wait=True)


# we have 6 PPW but only two are physical
#for dx in (1, 2, 3, 4, 5, 6):
for dx in (1, 2):
    pvput(":{}:TRG".format(dx),        "TRG_BUS" )    
    pvput(":{}:TRG:DX".format(dx),     "d0" )    
    pvput(":{}:TRG:SENSE".format(dx),  "rising")

    pvput(":{}:REPMODE".format(dx),       "CONT")

    pvput(":{}:PULSE".format(dx),      "INIT_LO")

    pvput(":{}:PULSE:WIDTH".format(dx), dx*2)
    pvput(":{}:PULSE:DELAY".format(dx), dx*2)
    pvput(":{}:PULSE:PERIOD".format(dx), dx*4)

        
epics.caput(dioen, 1)

