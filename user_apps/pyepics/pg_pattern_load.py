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

uut="acq1001_653"
site=int(os.getenv("SITE", "2"))
STL=os.getenv("STL", "/usr/local/CARE/STL/mustang-v8-left.stl")
TSCALE=int(os.getenv("TSCALE", "1"))
MODE=os.getenv("MODE", "LOOPWAIT")

print(f"UUT:{uut} SITE:{site} MODE:{MODE} STL:{STL}")

TRGDX = os.getenv("TRGDX", "d1")   # soft trigger
EDGE  = os.getenv("EDGE", "rising")

stlpv = epics.PV(f"{uut}:{site}:GPG:STL")

enpv = epics.PV(f"{uut}:{site}:GPG:ENABLE")
mode = epics.PV(f"{uut}:{site}:GPG:MODE")
tscale = epics.PV(f"{uut}:{site}:GPG:TIMESCALER")
trg = epics.PV(f"{uut}:{site}:TRG")
trgdx = epics.PV(f"{uut}:{site}:TRG:DX")
edge = epics.PV(f"{uut}:{site}:TRG:SENSE")

ln=0
with open(STL, "r") as fp:
	lines = fp.readlines()

lines.append(r"EOF\n")

enpv.put(0, wait=True)
trg.put("enable", wait=True)
trgdx.put(TRGDX, wait=True)
edge.put(EDGE, wait=True)

tscale.put(TSCALE, wait=True)
stlpv.put(lines, wait=True)

mode.put(MODE, wait=True)
enpv.put(1, wait=True)

epics.PV(f"{uut}:{site}:GPG:PULSE_DEF").put(os.path.basename(STL))




