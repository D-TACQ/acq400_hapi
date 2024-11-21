#!/usr/bin/env python3

import numpy as np
import epics
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('uut')
parser.add_argument('site')
args = parser.parse_args()

PVR = f'{args.uut}:{args.site}'
AMP=5
ramp_up = np.linspace(-AMP,AMP,1000)
ramp_dn = np.linspace(AMP,-AMP,1000)
cup = AMP*np.cos(np.linspace(0, np.pi, 1000))
sup = AMP*np.sin(np.linspace(0, np.pi, 1000))

epics.caput(f'{PVR}:AO:STEP:1', ramp_up)
epics.caput(f'{PVR}:AO:STEP:2', ramp_dn)
epics.caput(f'{PVR}:AO:STEP:3', cup)
epics.caput(f'{PVR}:AO:STEP:4', sup)

epics.caput(f'{args.uut}:0:AO:STEP:CURSOR', 0)


