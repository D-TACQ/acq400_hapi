#!/usr/bin/env python
'''
Created on 11 Jul 2021

@author: pgm

./user_apps/acq400/acq400_configure_transient.py  --pre=0 --post=20000 --demux=1 --trg=int,rising acq2106_188
'''


import acq400_hapi
import argparse
import subprocess
import numpy as np

def get_args():
    parser = argparse.ArgumentParser(description='configure multiple acq400')
    acq400_hapi.Acq400UI.add_args(parser, transient=True)
    parser.add_argument('uuts', nargs=1, help="uut ")
    return parser.parse_args()


def dump_data(chx, ix=0, stride=1, maxwords=32):
    ncol = 8
    col = 0

    print("shape chx)=[{},{}]".format(len(chx), len(chx[0])))
    for w in np.uint32(chx[ix][:maxwords:stride]):
        print('%08x' % w, end = '\n' if col==ncol else ',')
        if col == ncol:
            col = 0
        else:
            col += 1
    print("")
    
@acq400_hapi.timing
def uut_demux_channel_offload(shot_controller, uut):
    print("\nuut_demux_channel_offload")
    uut.s0.transient = "DEMUX=1"
    shot_controller.run_shot(soft_trigger=1)
    acq400_hapi.cleanup.sleep(1.0)
    dump_data(uut.read_channels(1))
 
@acq400_hapi.timing 
def uut_raw_offload(shot_controller, uut):
    print("\nuut_raw_offload")
    uut.s0.transient = "DEMUX=0"
    shot_controller.run_shot(soft_trigger=1)
    acq400_hapi.cleanup.sleep(1.0)
    dump_data(uut.read_channels(0))

@acq400_hapi.timing             
def uut_raw_channel_offload_local_demux(shot_controller, uut):
    print("\nuut_raw_channel_offload_local_demux showing auto local demux")
    uut.s0.transient = "DEMUX=0"
    shot_controller.run_shot(soft_trigger=1)
    acq400_hapi.cleanup.sleep(1.0)
    dump_data(uut.read_channels(1))
    
@acq400_hapi.timing    
def uut_bulk_offload_local_demux(shot_controller, uut): 
    print("\nuut_bulk_offload_local_demux showing auto local demux")
    uut.s0.transient = "DEMUX=0"
    shot_controller.run_shot(soft_trigger=1)
    acq400_hapi.cleanup.sleep(1.0)
    dump_data(uut.read_channels(0, localdemux=True), )
    
@acq400_hapi.timing             
def uut_raw_channel_offload_local_demux_list(shot_controller, uut):
    print("\nuut_raw_channel_offload_local_demux_list showing auto local demux")
    uut.s0.transient = "DEMUX=0"
    shot_controller.run_shot(soft_trigger=1)
    acq400_hapi.cleanup.sleep(1.0)
    chls = (1,2,3)
    chx = uut.read_channels(chls)
    for ch in chls:
        dump_data(chx, ix=ch-1)                
    
def run_main():
    args = get_args()
    uut = acq400_hapi.factory("{}".format(args.uuts[0]))
    acq400_hapi.Acq400UI.exec_args(uut, args)
    print("instantiate ShotController {}".format((uut,)))
    shot_controller = acq400_hapi.ShotController((uut,))
    tests = (uut_raw_offload, uut_demux_channel_offload, uut_raw_channel_offload_local_demux, uut_bulk_offload_local_demux, uut_raw_channel_offload_local_demux_list)
    
    try: 
        for test in tests:
            test(shot_controller, uut)

    except acq400_hapi.cleanup.ExitCommand:
        print("ExitCommand raised and caught")
    finally:
        print("Finally, going down")    



# execution starts here

if __name__ == '__main__':
    run_main()
