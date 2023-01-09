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
        

def main(args):
    uuts = [ acq400_hapi.factory(u) for u in args.uuts ]    

    acq400_stream.run_main(args)
    
def get_parser():
    parser = acq400_stream.get_parser()    
    parser.add_argument('--stl', default='./test.stl', type=str, help="GPG pulse pattern STL") 
    parser.add_argument('--es_enable', default=None, help="enable/disable Event Signature (default: no touch)")
    return parser

if __name__ == '__main__':
    main(get_parser().parse_args())


