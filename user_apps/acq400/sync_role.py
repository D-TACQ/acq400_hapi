#!/usr/bin/env python

import sys
import acq400_hapi
from acq400_hapi import intSI as intSI
import argparse
import time
import os
import signal
import threading

def disable_trigger(master):

    # print("WARNING: REMOVEME temporary fudge while we get the sync trigger right")
    # master.s0.SIG_SYNC_OUT_TRG_DX = 'd0'
    master.s0.SIG_SRC_TRG_0 = 'DSP0'
    master.s0.SIG_SRC_TRG_1 = 'DSP1'
    return None

def enable_trigger(master):
    master.s0.SIG_SRC_TRG_0 = 'EXT'
    master.s0.SIG_SRC_TRG_1 = 'STRIG'

def expand_role(args, urole):
    # fpmaster          # fpclk, fptrg
    # fpmaster,strg     # fpclk, strg
    # master            # mbclk, strg
    # master,fptrg      # mbclk, fptrg

    if urole == "fpmaster" or urole == "master,fptrg":
        args.external_trigger = True
    else:
        args.external_trigger = False

    if urole == "fpmaster,strg":
        args.postfix.append("TRG:DX=d1")
        return "fpmaster"
    if urole == "master,fptrg":
        args.postfix.append("TRG:DX=d0")
        return "master"
    return urole

def configure_slave(name, args, postfix):
    slave = acq400_hapi.Acq400(name)
    slave.s0.sync_role = "{} {} {} {}".format('slave', args.fclk, args.fin, " ".join(postfix))

def run_shot(args):
    master = acq400_hapi.Acq400(args.uuts[0])
    if args.enable_trigger:
        enable_trigger(master)
        return

    args.postfix = []       # master specials
    postfix = []            # common specials
    if args.clkdiv:
        args.postfix.append("CLKDIV={}".args.clkdiv)

    master.s0.sync_role = "{} {} {} {}".format(expand_role(args, args.toprole),
                                            args.fclk, args.fin, " ".join(args.postfix), " ".join(postfix))

    if args.external_trigger:
        disable_trigger(master)
    else:
        # print("WARNING: REMOVEME temporary fudge while we get the sync trigger right")
        # master.s0.SIG_SYNC_OUT_TRG_DX = 'd1'
        print ""
        # enable_trigger(master)

    # now run all the slave in parallel. We can do this because they do not share data.
    threads = []
    for uutname in args.uuts[1:]:
        t = threading.Thread(target=configure_slave, args=(uutname, args, postfix))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

def run_main():
    parser = argparse.ArgumentParser(description='set sync roles for a stack of modules')
    acq400_hapi.Acq400UI.add_args(parser, post=False)
    parser.add_argument('--enable_trigger', default=None, help="set this to enable the trigger all other args ignored")
    parser.add_argument('--toprole', default='master', help="role of top in stack")
    parser.add_argument('--fclk', default='1000000', help="sample clock rate")
    parser.add_argument('--fin',  default='1000000', help="external clock rate")
    parser.add_argument('--clkdiv', default=None, help="optional clockdiv")
    parser.add_argument('uuts', nargs='+', help="uut ")
    run_shot(parser.parse_args())



# execution starts here

if __name__ == '__main__':
    run_main()
