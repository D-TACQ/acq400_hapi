#!/usr/bin/env python

"""upload file to AWG for a one-shot play

data for upload is either File (host-local data file) or Rainbow, a test pattern.
assumes that clocking has been pre-assigned.
"""



import sys
import acq400_hapi
from acq400_hapi import awg_data
import argparse
if sys.version_info < (3, 0):
    from future import builtins
    from builtins import input
import numpy as np


def load_awg(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    shot_controller = acq400_hapi.ShotController([uut])

    if args.clear_autorearm:
        uut.s1.playloop_maxshot = '1'
        print("allow system to run final shot and return to idle")
    else:
        if args.awg_extend > 1:
            data = np.fromfile(args.file, dtype=np.int32)
            new_awg = np.tile(data, (1,args.awg_extend))
            uut.load_awg(new_awg, autorearm=False)
            return None

        work = awg_data.RunsFiles(uut, args.file.split(","))
        _autorearm = True if args.autorearm == 1 else False
        work.load(autorearm=_autorearm)
        for f in work.load():
            print("Loaded %s" % (f))
            shot_controller.run_shot(soft_trigger= True if args.trg=='int' else False)

def get_parser():
    parser = argparse.ArgumentParser(description='acq400 simple awg demo')
    parser.add_argument('--file', default="", help="file to load")
    parser.add_argument('--autorearm', default=0, type=int, help="enable autorearm mode")
    parser.add_argument('--clear_autorearm', default=0, help="clear previous autorearm mode")
    parser.add_argument('--trg', default="int", help='trg "int|ext rising|falling"')
    parser.add_argument('--awg_extend', default=1, type=int, help='Number of times the AWG is repeated.')
    parser.add_argument('uuts', nargs=1, help="uut ")
    return parser

if __name__ == '__main__':
    load_awg(get_parser().parse_args())


