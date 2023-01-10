#!/usr/bin/env python3

''' run_AquadB_movement [ --monitor VALUE] [acq400_upload opts] uut  ...

Run a stream capture while monitoring AquadB position.
   WAIT_START: wait for position to change
   WAIT_END : wait for position to stop changing

The UUT is assumed to trigger a stimulator box that will run a movement simulation.
OR, it could be a real movement. We don't care.



'''

import acq400_hapi
import argparse
import time
import os
import sys
import numpy as np

sys.path.append(os.path.dirname(os.path.realpath('../../user_apps')))

from  user_apps.acq400 import acq400_stream_multi

from enum import Enum

class AquadB_callback:
    State = Enum('State', ["WaitCountActive", "WaitCountStop", "Finished"])
    def __init__(self, args, uut):
        self.state = AquadB_callback.State.WaitCountActive
        self.args = args
        self.uut = uut
        self.count = uut.s1.QEN_COUNT
        self.count_unchanged = 0
        pass

    def __call__(self):        
        newcount = self.uut.s1.QEN_COUNT
        if newcount == self.count:
            self.count_unchanged += 1                        
        else:
            self.count_unchanged = 0
            
        if self.state == AquadB_callback.State.WaitCountActive and self.count_unchanged == 0:
            self.state = AquadB_callback.State.WaitCountStop
        elif self.state == AquadB_callback.State.WaitCountStop and self.count_unchanged > 2:
            self.state = AquadB_callback.State.Finished


        print("AquadB_callback {} {}".format(self.state.name, newcount))
        self.count = newcount
        return self.state == AquadB_callback.State.Finished

def load_stim(uut, dwg):
    uut.load_awg(np.fromfile(dwg, dtype=np.uint32))
    pc = 0
    while acq400_hapi.intpv(uut.s1.AWG_ACTIVE) != 1:
        if pc > 1:
            print("polling for AWG_ACTIVE")
        time.sleep(1)
        pc += 1
    uut.s1.dio422_TxEN = 1

def main(args):
    uut = acq400_hapi.factory(args.uuts[0])

    if args.stim is not None:
        if args.dwg is None:
            print("ERROR: no dwg to load")
            return
        args.uut_stim = acq400_hapi.factory(args.stim)
        load_stim(args.uut_stim, args.dwg)

    args.callback = AquadB_callback(args, uut)
    acq400_stream_multi.run_stream(args)
#    while args.callback() == False:
#        time.sleep(1)

def get_parser():
    parser = acq400_stream_multi.get_parser()
#    parser = argparse.ArgumentParser(description='run_AquadB_movement')
#    parser.add_argument('uut', help="AquadB receiver, to monitor")
    parser.add_argument('--stim', default=None, help='stimulator uut')
    parser.add_argument('--dwg', default=None, help='stimulator dwg file to load')

    return parser

if __name__ == '__main__':
    main(get_parser().parse_args())


