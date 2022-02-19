#!/usr/bin/env python3
'''
Created on 14 Aug 2020

@author: pgm
'''

import acq400_hapi
from acq400_hapi import intSIAction
from acq400_hapi import intSI
import argparse
import threading
import os
import re
import sys

def acq2106_wr_reset(args):
    args.uuts = [ acq400_hapi.Acq2106(u, has_comms=False, has_wr=True) for u in args.uut ]
    
    for uut in args.uuts:
        uut.cC.WR_WRTT0_RESET = 1


def run_main():
    parser = argparse.ArgumentParser(description='acq2106_wr_reset')
    parser.add_argument('uut', nargs='+', help="uuts")
    acq2106_wr_reset(parser.parse_args())


# execution starts here

if __name__ == '__main__':
    run_main()
