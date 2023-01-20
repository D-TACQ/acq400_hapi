#!/usr/bin/python

'''
configures PWM on UUT

'''

import epics
import time
import sys
import os

UUT=os.getenv('IOC_HOST')
SITE=5

if len(sys.argv) == 2:
    UUT = sys.argv[1]

#acq2106_355:5:PPW:1:TRG :DX :SENSE
#acq2106_355:5:PPW:1:PULSE:ICOUNT OCOUNT GP REPS
#acq2106_355:5:PPW:1:PULSE

root = "{}:{}:PPW".format(UUT, SITE)

def pvput(suffix, value):
    name = root+suffix
    print("{} {}".format(name, value))
    epics.caput(name, value)

dioen = "{}:{}:DIO:ENABLE".format(UUT, SITE)

epics.caput(dioen, 0)

for dx in (1, 2, 3, 4, 5, 6):
    pvput(":{}:TRG".format(dx),        "TRG_BUS")    
    pvput(":{}:TRG:DX".format(dx),     "d3" if dx==2 else "d2")    
    pvput(":{}:TRG:SENSE".format(dx),  "rising")

    pvput(":{}:REPS".format(dx),       10 if dx==2 else 1)

    pvput(":{}:PULSE".format(dx),      "INIT_LO")
    pvput(":{}:PULSE:ICOUNT".format(dx), 1)
    pvput(":{}:PULSE:OCOUNT".format(dx), 50)
    pvput(":{}:PULSE:GP".format(dx),   2047 if dx==2 else 51)

        
epics.caput(dioen, 1)

