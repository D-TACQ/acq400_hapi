#!/usr/bin/env python

import sys
import acq400_hapi
from acq400_hapi import intSI as intSI
import argparse
import time
import os
import signal
import threading




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
    elif urole == "master,fptrg":
        args.postfix.append("TRG:DX=d0")
        
    args.postfix.append("TRG:SENSE={}".format(args.trgsense))
    return urole.split(",")[0]

def configure_slave(name, args, postfix):
    slave = acq400_hapi.Acq400(name)
    slave.s0.sync_role = "{} {} {} {}".format('slave', args.fclk, args.fin, " ".join(postfix))
    if args.downstream_bypass:
        slave.s0.SYS_CLK_BYPASS = 1

def set_sync_role(args):
    master = acq400_hapi.Acq400(args.uuts[0])
    
    if args.enable_trigger == 1:
        master.enable_trigger()
        return

    args.postfix = []       # master specials
    postfix = []            # common specials
    if args.clkdiv:
        args.postfix.append("CLKDIV={}".args.clkdiv)

    master.s0.sync_role = "{} {} {} {}".format(expand_role(args, args.toprole),
                                            args.fclk, args.fin if not args.toprole=="master" else "", 
                                            " ".join(args.postfix), " ".join(postfix))
   
    if args.si5326_bypass:
        master.s0.si5326bypass = '1'
    if args.downstream_bypass:
        master.s0.SIG_SYNC_OUT_CLK_DX = 'd1'

    if args.external_trigger and len(args.uuts) > 1:
        master.disable_trigger()
    else:
        # print("WARNING: REMOVEME temporary fudge while we get the sync trigger right")
        # master.s0.SIG_SYNC_OUT_TRG_DX = 'd1'
        print("")
        # enable_trigger(master)

    # now run all the slave in parallel. We can do this because they do not share data.
    threads = []
    for uutname in args.uuts[1:]:
        t = threading.Thread(target=configure_slave, args=(uutname, args, postfix))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
        
    if args.enable_trigger == 99:
        master.enable_trigger()

def run_main():
    parser = argparse.ArgumentParser(description='set sync roles for a stack of modules')
    acq400_hapi.Acq400UI.add_args(parser, post=False)
    parser.add_argument('--enable_trigger', default=0, help="0:leave disabled, 1 enable and drop out, 99 to enable at end")
    parser.add_argument('--toprole', default='master', help="role of top in stack")
    parser.add_argument('--fclk', default='1000000', help="sample clock rate")
    parser.add_argument('--fin',  default='1000000', help="external clock rate")
    parser.add_argument('--clkdiv', default=None, help="optional clockdiv")
    parser.add_argument('--downstream_bypass', default=0, type=int, help="provide full rate clock downstream")
    parser.add_argument('--si5326_bypass', default=0, type=int, help="bypass Si5326")
    parser.add_argument('--trgsense', default='rising', help="trigger sense rising unless falling specified")
    parser.add_argument('uuts', nargs='+', help="uut ")
    set_sync_role(parser.parse_args())



# execution starts here

if __name__ == '__main__':
    run_main()
