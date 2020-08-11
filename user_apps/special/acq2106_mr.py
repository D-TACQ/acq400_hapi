#!/usr/bin/env python

"""
configure and run a Multi Rate (MR) shot on one or more UUTs
pre-requisite: transient capture configured on all boxes

usage: acq2106_mr.py uut [uut2..]

example:
./user_apps/special/acq2106_mr.py --stl user_apps/STL/acq2106_mr3.stl --set_arm=1 acq2106_182

run_gpg

positional arguments:
  uut                   uut

optional arguments:
  -h, --help            show this help message and exit
  --trg TRG             trigger fp|soft|softloop|softonce
  --clk CLK             clk int|dX|notouch
  --mode MODE           mode
  --disable DISABLE     1: disable
  --stl STL             stl file
  --waterfall WATERFALL
                        d0,d1,d2,d3 waterfall [interval,hitime]
  --trace TRACE         trace wire protocol
  --hdmi_master HDMI_MASTER
                        clk, trg and gpg drive HDMI outputs
"""

import acq400_hapi
from acq400_hapi import intSIAction
from acq400_hapi import intSI
import argparse
import threading
import os
import re
import sys

"""
denormalise_stl(args): convert from usec to clock ticks. round to modulo decval
"""
def denormalise_stl(args):
    lines = args.stl.splitlines()
    args.literal_stl = ""
    args.stl_literal_lines = []
    for line in lines:
        if line.startswith('#') or len(line) < 2:
            if args.verbose:
                print(line)
        else:
            action = line.split('#')[0]

            if action.startswith('+'): # support relative increments
                delayp = '+'
                action  = action[1:]
            else:
                delayp = ''

            delay, state = [int(x) for x in action.split(',')]
            delayk = int(delay * args.Fclk / 1000000)
            delaym = delayk - delayk % args.MR10DEC
            state = state << args.evsel0
            elem = "{}{:d},{:02x}".format(delayp, delaym, state)
            args.stl_literal_lines.append(elem)
            if args.verbose:
                print(line)

    return "\n".join(args.stl_literal_lines)

NONE = 'NONE'

def selects_trg_src(uut, src):
    def select_trg_src():
        uut.s0.SIG_SRC_TRG_0 = src
    return select_trg_src

def allows_one_wrtd(uut):
    def allow_one_wrtd():
        uut.s0.SIG_SRC_TRG_0 = 'WRTT0'
        uut.cC.WRTD_TX = 1
        uut.cC.wrtd_tx = 1
    return allow_one_wrtd

def run_postprocess_command(cmd, uut_names):
    syscmd = "{} {}".format(cmd, " ".join(uut_names))
    print("run {}".format(syscmd))
    os.system(syscmd)

def open_safe(fn, mode):
    try:
        return open(fn, mode)
    except:
        return open("{}/{}".format(os.getenv("HAPIDIR", '.'), fn), mode)

def tune_action(u):
    def _tune_action():
        u.s0.si5326_tune_phase = 1
    return _tune_action


def _tune_up_mt(args):
    thx = []
    for u in args.uuts:
        if args.tune_si5326 == 2:
            if int(u.cC.Si5326_TUNEPHASE_OK.split(" ")[1]) == 1:
                print("{} TUNEPHASE_OK, skip".format(u.uut))
                continue

        print("si5326_tune_phase on {}, this may take 30s".format(u.uut))
        th = threading.Thread(target=tune_action(u))
        th.start()
        thx.append(th)

    for t in thx:
        t.join()

def tune_up_mt(args):
    if args.tune_si5326 == 0:
        return

    _tune_up_mt(args)

    if args.tune_si5326 == -1:
        sys.exit('tuneup done')

def tee_up(args):
    master = args.uuts[0]
    with open_safe(args.stl, 'r') as fp:
        args.stl = fp.read()

    lit_stl = denormalise_stl(args)

    master.s0.SIG_SRC_TRG_0 = NONE

    trg0_src = args.trg0_src.split(',')
    if trg0_src[0] == "WRTT0":
        master.s0.wr_trg_src = '1,{},1'.format(1 if len(trg0_src)==2 and trg0_src[1]=='RP' else 0)
        master.cC.WRTD_TX = 0
        master.cC.WRTD_DELTA_NS = args.WRTD_DELTA_NS
        master.cC.wrtd_commit_tx = 1
        args.rt = allows_one_wrtd(master)
    else:
        master.s0.SIG_SRC_TRG_0 = 'EXT'
        args.rt = selects_trg_src(master, args.trg0_src)

    for u in args.uuts[1:]:
        u.s0.SIG_SRC_TRG_0 = "WRTT0"

    for u in args.uuts:
        acq400_hapi.Acq400UI.exec_args(u, args)
        u.s0.gpg_trg = '1,0,1'
        u.s0.gpg_clk = '1,1,1'
        u.s0.GPG_ENABLE = '0'
        u.load_gpg(lit_stl, args.verbose > 1)
        u.set_MR(True, evsel0=args.evsel0, evsel1=args.evsel0+1, MR10DEC=args.MR10DEC)
        u.s0.set_knob('SIG_EVENT_SRC_{}'.format(args.evsel0), 'GPG')
        u.s0.set_knob('SIG_EVENT_SRC_{}'.format(args.evsel0+1), 'GPG')
        u.s0.GPG_ENABLE = '1'
        if args.set_shot is not None:
            u.s1.shot = args.set_shot

def run_mr(args):
    args.uuts = [ acq400_hapi.Acq2106(u, has_comms=False, has_wr=True) for u in args.uut ]
    tune_up_mt(args)
    shot_controller = acq400_hapi.ShotControllerWithDataHandler(args.uuts, args)

    if args.set_arm != 0:
        tee_up(args)
        shot_controller.run_shot(remote_trigger=args.rt)
    else:
        shot_controller.handle_data(args)

    if args.get_epics4:
        run_postprocess_command(args.get_epics4, args.uut)
    if args.get_mdsplus:
        run_postprocess_command(args.get_mdsplus, args.uut)


def run_main():
    parser = argparse.ArgumentParser(description='acq2106_mr')
    acq400_hapi.Acq400UI.add_args(parser, transient=True)
    acq400_hapi.ShotControllerUI.add_args(parser)
    parser.add_argument('--stl', default='./STL/acq2106_mr00.stl', type=str, help='stl file')
    parser.add_argument('--Fclk', default=40*intSI.DEC.M, action=intSIAction, help="base clock frequency")
    parser.add_argument('--WRTD_DELTA_NS', default=50*intSI.DEC.M, action=intSIAction, help='WRTD trigger delay')
    parser.add_argument('--trg0_src', default="EXT", help="trigger source, def:EXT opt: WRTT0, WRTT0,RP")
    parser.add_argument('--tune_si5326', default=1, type=int, help="tune_si5326 (takes 60s), default:1")
    parser.add_argument('--set_arm', default='0', type=int, help="1: set arm" )
    parser.add_argument('--set_shot', default=None, type=int, help="set this shot number on all UUTS before shot")
    parser.add_argument('--evsel0', default=4, type=int, help="dX number for evsel0")
    parser.add_argument('--MR10DEC', default=8, type=int, help="decimation value")
    parser.add_argument('--verbose', type=int, default=0, help='Print extra debug info.')
    parser.add_argument('--get_epics4', default=None, type=str, help="run script [args] to store EPICS4 data")
    parser.add_argument('--get_mdsplus', default=None, type=str, help="run script [args] to store mdsplus data")
    parser.add_argument('uut', nargs='+', help="uuts")
    run_mr(parser.parse_args())


# execution starts here

if __name__ == '__main__':
    run_main()
