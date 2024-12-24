#!/usr/bin/env python

import epics
import os
import sys
import time

class Aggregate:
    pass

# aggregate all PV instances in one collection..
pva = Aggregate

CHMAX = int(os.getenv("CHMAX", 4))
UUT = os.getenv("UUT", "acq2106_407")
AO_SITE = os.getenv("AO_SITE", "5")

AO_STEPS = []


def connect_all_pvs():
    global pva
    
    pva.sig_src_trg0 = epics.PV(f'{UUT}:0:SIG:SRC:TRG:0')
    pva.sig_src_trg1 = epics.PV(f'{UUT}:0:SIG:SRC:TRG:1')
    pva.soft_trigger = epics.PV(f'{UUT}:SIG:SOFT_TRIGGER')

    pva.state = epics.PV(f'{UUT}:MODE:CONTINUOUS:STATE')

    pva.AO_OUTPUTS = []
    pva.AO_STEP_EN = []
    pva.AO_STEPS   = []
    pva.nostep = epics.PV(f'{UUT}:0:AO:STEP:CURSOR_NOSTEP')
    pva.CURSOR = epics.PV(f'{UUT}:0:AO:STEP:CURSOR')

    for ic in range(CHMAX):
        pva.AO_OUTPUTS.append(epics.PV(f'{UUT}:{AO_SITE}:AO:SLOW_SET:CH:{ic+1}'))
        pva.AO_STEP_EN.append(epics.PV(f'{UUT}:{AO_SITE}:AO:STEP:{ic+1}:EN'))
        pva.AO_STEPS.append(epics.PV(f'{UUT}:{AO_SITE}:AO:STEP:{ic+1}'))


def output():
    global step
    try:
        for ic in range(CHMAX):
            pva.AO_OUTPUTS[ic].put(AO_STEPS[ic][step])
        step += 1
        pva.CURSOR.put(step)
    except:
        print(f'output finished at {step}')
        sys.exit(0)


connect_all_pvs()
print(f'Stub external trigger and internal step')
pva.sig_src_trg0.put('NONE')
pva.sig_src_trg1.put('NONE')
pva.nostep.put('NOSTEP')


print(f'dac_step_scan.py out of IOC scanner {CHMAX} channels')

step = 0;
old_state = None
the_state = 0

while True:
    the_state = pva.state.get()
    if the_state == 1 :
        break
    if the_state != old_state:
        print(f'state:{the_state}')
        old_state = the_state
    time.sleep(0.1)

print('enable trigger1 source and fire soft trigger')
pva.sig_src_trg1.put("STRIG")
pva.soft_trigger.put(1)

# We pick up up the lists of steps late after ext script has set them, ditto, disable internal IOC stepping
for ic in range(CHMAX):
#    AO_STEPS.append([ int(ii*32768/10) for ii in epics.PV(f"acq2106_407:5:AO:STEP:{ic+1}").value])
    AO_STEPS.append(pva.AO_STEPS[ic].value)
    pva.AO_STEP_EN[ic].put(0)


print(f'dac_step_scan.py out of IOC scanner for {len(AO_STEPS[0])} steps on {CHMAX} channels')
output()
print(f'Enable external trigger source')
pva.sig_src_trg0.put('EXT')

ii = 0
with open("/dev/acq400.0.bqf", "r") as bq:
    while True:
        bn = bq.readline().strip()
        output()
        ii += 1
        print('.', end='' if ii%20 != 0 else '\n', flush=True)


