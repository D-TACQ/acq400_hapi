#!/usr/bin/python
import time
import epics
import sys
import os

uut='acq1001_653'
site='2'
SLEEP=float(os.getenv("SLEEP", "0.1"))
EIGHTBITS=int(os.getenv("EIGHTBITS", 8))

epics.PV(f"{uut}:{site}:DIO_MODE").put("IMM")

eightbits = [ epics.PV(f"{uut}:{site}:DO:{b}") for b in range(1,EIGHTBITS+1) ]

while True:
    for b in range(0,len(eightbits)):
        eightbits[b].put(1, wait=True)
        time.sleep(SLEEP)
        eightbits[b].put(0, wait=True)



