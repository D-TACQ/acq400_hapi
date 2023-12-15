#!/usr/bin/env python

"""
acq2106_wrpg_clkout_demo.py ... configure demo clock output on SYNC_OUT CLK


"""

import argparse
import math
import time
import acq400_hapi

def wrpg_clkout_demo(args):
    uut = acq400_hapi.Acq2106(args.uut[0])
    uut.s0.SIG_SYNC_OUT_CLK = 'CLK'
    uut.s0.SIG_SYNC_OUT_CLK_DX = 'd6'

    uut.s5.CLK = 'external'
    uut.s5.CLK_DX = 'd1'
    uut.s5.CLKDIV = args.clkdiv

    fset = acq400_hapi.freq(uut.s0.SIG_CLK_MB_FREQ)/args.clkdiv

    converged = False
    while not converged:
        fout = acq400_hapi.freq(uut.s0.SIG_CLK_S5_FREQ)
        converged =  (fset/fout if fset < fout else fout/fset) > 0.95
        print("set {:.0f} fout {:.0f} {}".\
                    format(fset, fout, "OK" if converged else "waiting.."))


    if args.loopback:
        uut.s0.SIG_SRC_CLK_0 = 'HDMI'
        if not uut.s0.SIG_SYNC_BUS_OUT_CABLE_DET:
            print("ERROR cable not connected")
            return
        converged = False
        while not converged:
            fin = acq400_hapi.freq(uut.s0.SIG_CLK_EXT_FREQ)
            converged =  (fin/fout if fin < fout else fout/fin) > 0.95
            print("out {:.0f} back {:.0f} {}".\
                    format(fout, fin, "OK" if converged else "waiting.."))


def get_parser():
    parser = argparse.ArgumentParser(description=" wrpg clkout demo")
    parser.add_argument('--loopback', default=0, type=int, help="use loopback cable")
    parser.add_argument('--clkdiv', default=20, type=int, help="clock divider value")
    parser.add_argument('uut', nargs=1, help='uut')
    return parser

if __name__ == '__main__':
    wrpg_clkout_demo(get_parser().parse_args())

