#!/usr/bin/python

'''
configures ABS and PERIOD TRIGGER on UUT

'''

import epics
import time
import sys
import os

UUT=os.getenv('IOC_HOST')

if len(sys.argv) == 2:
    UUT = sys.argv[1]

root = "{}:".format(UUT)

def pvput(suffix, value):
    name = root+suffix
    print("{} {}".format(name, value))
    epics.caput(name, value)

for site in (1, 2):
    pvput("{}:QEN:ABS_TRG:EN".format(site), 0)
    pvput("{}:QEN:PRD_TRG:EN".format(site), 0)
    pvput("{}:QEN:ABS_TRG".format(site),            1000)
    pvput("{}:QEN:PRD_TRG".format(site),          100000)
    pvput("{}:QEN:PRD_TRG_HYST".format(site),    -100000)
    pvput("{}:QEN:ABS_TRG:EN".format(site), 1)
    pvput("{}:QEN:PRD_TRG:EN".format(site), 1)

    
