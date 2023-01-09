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

import os
import sys
sys.path.append(os.path.dirname(os.path.realpath('../../user_apps')))

from  user_apps.acq400 import acq400_stream

from enum import Enum
       
class AquadB_callback:
    State = Enum('State', ["WaitCountActive", "WaitCountStop", "Finished"])
    def __init__(self, uut):
        self.state = AquadB_callback.State.WaitCountActive
        self.uut = uut
        self.count = uut.s1.QEN_COUNT
        self.count_unchanged = 0
        pass
    
    def __call__(self):
        newcount = self.uut.s1.QEN_COUNT
        if newcount != self.count:
            self.count_unchanged += 1
        else:
            self.count_unchanged = 0
        if self.state == AquadB_callback.State.WaitCountActive and self.count_unchanged > 2:
            self.state = AquadB_callback.State.WaitCountStop
        elif self.state == AquadB_callback.State.WaitCountStop and self.count_unchanged == 0:
            self.state = AquadB_callback.State.Finished
            
            
           
        print("AquadB_callback {} {}".format(self.state.name, newcount))
        self.count = newcount
        return self.state == AquadB_callback.State.Finished
     

def main(args):
    uut = acq400_hapi.factory(args.uuts[0]) 
    args.callback = AquadB_callback(uut)
    acq400_stream.run_stream(args)
    
def get_parser():
    parser = acq400_stream.get_parser()    
    parser.add_argument('--stl', default='./test.stl', type=str, help="GPG pulse pattern STL") 
    parser.add_argument('--es_enable', default=None, help="enable/disable Event Signature (default: no touch)")
    return parser

if __name__ == '__main__':
    main(get_parser().parse_args())


