#!/usr/bin/python

'''
trigger_when_uut_armed.py LOC UUT

LOC is a signal generator (eg DWG) and is HDMI master
UUT is an HDMI slave

Program waits for UUT to achieve state ARM, then fires a SOFT_TRIGGER

The SOFT_TRIGGER kicks off the LOC DWG and UUT CAPTURE.

Make me a resident service with:

procServ 12355 /mnt/local/trigger_when_uut_armed.py $(hostname) UUT

Or run on a remote box .. anywhere with py epics

while [ 1 ]; do trigger_when_uut_armed.py STIM UUT


'''

import epics
import time
import sys

UUT= 'acq2106_355'
LOC= 'acq2106_274'

if len(sys.argv) == 3:
    LOC = sys.argv[1]
    UUT = sys.argv[2]


TRIGGER_REQUEST = False

def onChanges(pvname=None, value=None, char_value=None, **kw):
    global TRIGGER_REQUEST
    print('PV Changed! ', pvname, char_value, time.ctime())
    if char_value == '1':
        print("Trigger {}".format(trigger))
        TRIGGER_REQUEST = True


trigger  = epics.PV("{}:SIG:SOFT_TRIGGER".format(LOC), auto_monitor=True)
statemon = epics.PV("{}:MODE:CONTINUOUS:STATE".format(UUT))
statemon.add_callback(onChanges)

while True:
    if TRIGGER_REQUEST:
        trigger.put(1, wait=True)
        print("Trigger done")
        TRIGGER_REQUEST = False
    time.sleep(1)




