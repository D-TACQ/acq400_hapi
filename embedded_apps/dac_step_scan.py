#!/usr/bin/env python

import epics
import os
import sys
import time

CHMAX = int(os.getenv("CHMAX", 4))

AO_STEPS = []
AO_STEP_EN = []
AO_OUTPUTS = []

#class ScanPvSet:
#    def __init__(self, uutname, aosite, nchan):
#        self.


sig_src_trg0 = epics.PV("acq2106_407:0:SIG:SRC:TRG:0")
sig_src_trg1 = epics.PV("acq2106_407:0:SIG:SRC:TRG:1")
soft_trigger = epics.PV("acq2106_407:SIG:SOFT_TRIGGER")

state = epics.PV("acq2106_407:MODE:CONTINUOUS:STATE")

for ic in range(CHMAX):
    AO_OUTPUTS.append(epics.PV(f'acq2106_407:5:AO:SLOW_SET:CH:{ic+1}'))
    AO_STEP_EN.append(epics.PV(f'acq2106_407:5:AO:STEP:{ic+1}:EN'))

print(f'Stub external trigger and internal step')
sig_src_trg0.put('NONE')
sig_src_trg1.put('NONE')
epics.PV("acq2106_407:0:AO:STEP:CURSOR_NOSTEP").put("NOSTEP")


CURSOR = epics.PV("acq2106_407:0:AO:STEP:CURSOR")

state = epics.PV("acq2106_407:MODE:CONTINUOUS:STATE")

print(f'dac_step_scan.py out of IOC scanner {CHMAX} channels')


def output():
    global step
    try:
        for ic in range(CHMAX):
            AO_OUTPUTS[ic].put(AO_STEPS[ic][step])
        step += 1
        CURSOR.put(step)
    except:
        print(f'output finished at {step}')
        sys.exit(0)

step = 0;

old_state = None
the_state = 0

while True:
    the_state = state.get()
    if the_state == 1 :
        break
    if the_state != old_state:
        print(f'state:{the_state}')
        old_state = the_state
    time.sleep(0.1)

print('enable trigger1 source and soft trigger')
sig_src_trg1.put("STRIG")
soft_trigger.put(1)

# We pick up up the lists of steps late after ext script has set them, ditto, disable internal IOC stepping
for ic in range(CHMAX):
#    AO_STEPS.append([ int(ii*32768/10) for ii in epics.PV(f"acq2106_407:5:AO:STEP:{ic+1}").value])
    AO_STEPS.append(epics.PV(f"acq2106_407:5:AO:STEP:{ic+1}").value)
    AO_STEP_EN[ic].put(0)


print(f'dac_step_scan.py out of IOC scanner for {len(AO_STEPS[0])} steps on {CHMAX} channels')
output()
print(f'Enable external trigger source')
sig_src_trg0.put('EXT')

ii = 0
with open("/dev/acq400.0.bqf", "r") as bq:
    while True:
        bn = bq.readline().strip()
        output()
        ii += 1
        print('.', end='' if ii%20 != 0 else '\n', flush=True)


