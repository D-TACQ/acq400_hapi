#!/usr/bin/env python3
import time
import epics
import sys
import os

uut = os.getenv("UUT")
if not uut:
    uut = os.getenv("IOC_HOST")

if not uut:
    print("ERROR: UUT not defined")
    os._exit(1)

site=os.getenv("SITE", "2")
SLEEP=float(os.getenv("SLEEP", "0.1"))
EIGHTBITS=int(os.getenv("EIGHTBITS", 8))

epics.PV(f"{uut}:{site}:DIO_MODE").put("IMM")

eightbits = [ epics.PV(f"{uut}:{site}:DO:{b}") for b in range(1,EIGHTBITS+1) ]

while True:
    for b in range(0,len(eightbits)):
        eightbits[b].put(1, wait=True)
        time.sleep(SLEEP)
        eightbits[b].put(0, wait=True)



