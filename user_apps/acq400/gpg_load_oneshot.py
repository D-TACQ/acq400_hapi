#!/usr/bin/env python3

import acq400_hapi
import argparse
import os
from subprocess import call


def main(args):
    uut  = acq400_hapi.Acq400(args.uut, monitor=False)

    uut.s1.RGM = 'RGM'
    uut.s0.gpg_enable = 0
    uut.s0.GPG_TRG = 'external'
    uut.s0.GPG_TRG_DX = 'd0'
    uut.s0.GPG_TRG_SENSE = 'rising'
    uut.s0.GPG_MODE = 'LOOPWAIT'
    uut.s0.gpg_enable = 1
    uut.s0.TRANSIENT_POST = 400000

    stl = get_stl(args.stl)
    uut.load_gpg(stl)
    
    os.system("user_apps/acq400/acq400_upload.py --pre=None --capture=1 --remote_trigger=EXT --plot_data=-1 --pre=0 --post=4000000 " + args.uut)

def get_stl(stl):
    with open (stl, "r") as stl_file:
        stl = stl_file.read()
    return stl
    
def get_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--stl', default='./test.stl', type=str, help="Which STL file to load")
    parser.add_argument('uut', help="Names of uut")
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    main(get_args())


