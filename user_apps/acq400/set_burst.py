#!/usr/bin/env python

"""
set burst mode
run_gpg.py [opts] uut

usage: set_burst.py [-h] [--rgm RGM] [--mbclk MBCLK] [--dx DX] [--gpg GPG]
                [--sense SENSE] [--rtm_translen RTM_TRANSLEN]
                [--post POST] [--trg TRG] [--hdmi_slave HDMI_SLAVE]
                [--es_enable ES_ENABLE] [--trace TRACE] [--demux DEMUX]
                uuts [uuts ...]

set_burst mode

positional arguments:
  uuts                  uut

optional arguments:
  -h, --help            show this help message and exit
  --rgm RGM             mode RGM|RTM
  --mbclk MBCLK         notouch|FIN,FOUT
  --dx DX               dx d0|d1|d2
  --gpg GPG             source from gpg on|off
  --sense SENSE         rising|falling
  --rtm_translen RTM_TRANSLEN
                        transient length
  --post POST           shot length
  --trg TRG             shot trigger triplet
  --hdmi_slave HDMI_SLAVE
                        no: use FPTRG, yes: use HDMI trg on d0, full=use all 4
                        lines
  --es_enable ES_ENABLE
                        0 disables Event Signature
  --trace TRACE         1: enable command trace
  --demux DEMUX         0: do not demux
"""

import sys
import acq400_hapi
import argparse
import re
import time
import math

def set_hdmi_slave_full(uut):
    uut.s0.SIG_SRC_CLK_0 = 'HDMI'
    uut.s0.SIG_SRC_TRG_0 = 'HDMI_TRG'
    uut.s0.SIG_SRC_SYNC_0 = 'HDMI'
    uut.s0.SIG_EVENT_SRC_3 = 'HDMI_SYNC'
    uut.s0.SIG_EVENT_SRC_1 = 'HDMI_GPIO'
    uut.s0.SYS_CLK_FPMUX = 'ZCLK'
    uut.s0.SIG_ZCLK_SRC = 'CLK.d0'

def set_mbclk(uut, f2):
    if len(f2) == 2:
        fin = int(f2[0])
        fout = int(f2[1])
    else:
        fin = 0
        fout = int(f2[0])
    uut.s0.SIG_CLK_MB_FIN = fin
    uut.s0.SIG_CLK_MB_SET = 2*fout
    time.sleep(1)
    uut.s0.SIG_CLK_MB_SET = fout
    settled = False

    while not settled:
        actual = float(uut.s0.SIG_CLK_MB_FREQ.split(' ')[1])
        if math.fabs(actual - fout) < 10000:
            settled = True
        print("mb_clk set:{} actual:{} {}".format(fout, actual, 'OK' if settled else ''))
        if not settled:
            time.sleep(1)
        

def configure_bm(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]

    for u in uuts:
        u.s0.trace      = args.trace
        u.s1.trace      = args.trace

        u.s0.GPG_ENABLE = '0'       # needed if running set.burst multiple times
        u.clear_counters()          # makes COUNTERS opi easier to read
        u.s1.trg        = args.trg
        u.s1.RGM        = args.rgm
        u.s1.RGM_DX     = args.dx
        u.s1.RGM_SENSE  = args.sense
        u.s1.es_enable  = args.es_enable
        u.s1.RTM_TRANSLEN = args.rtm_translen if args.rgm == 'RTM' else 0
        u.s1.rtm_translen = args.rtm_translen if args.rgm == 'RTM' else 0
        
        if args.config_only:
            continue

        u.s0.transient  = 'POST={} DEMUX={}'.format(args.post, args.demux)
        u.s0.set_knob('SIG_SRC_TRG_1', 'GPG1' if args.gpg == 'on' and args.dx == 'd1' else 'STRIG')

        if args.hdmi_slave.startswith('full'):
            set_hdmi_slave_full(u)
        else:
            u.s0.set_knob('SIG_SRC_TRG_0', 'GPG0' if args.gpg == 'on' and args.dx == 'd0' else 'EXT' if args.hdmi_slave == 'no' else 'HDMI_TRG')

        if args.mbclk != 'notouch':
            set_mbclk(u, args.mbclk.split(','))
       
        u.s0.set_arm = 1

    if args.config_only:
        print("config_only: DONE")
        return

    for u in uuts:
        u.statmon.wait_armed()

    # warning: this is a RACE for the case of a free-running trigger and multiple UUTs
    if args.gpg == 'on':
        for u in uuts:
            u.s0.GPG_ENABLE = '1'
        
    if args.trg == '1,1,1':
        for u in uuts:
            u.s0.soft_trigger
    


def run_main():
    parser = argparse.ArgumentParser(description='set_burst mode')    
    parser.add_argument('--rgm', default='RTM', type=str, help="mode RGM|RTM")
    parser.add_argument('--mbclk', default='notouch', type=str, help="notouch|FIN,FOUT")
    parser.add_argument('--dx', default='d0', type=str, help='dx d0|d1|d2')
    parser.add_argument('--gpg', default='off', type=str, help='source from gpg on|off')
    parser.add_argument('--sense', default='rising', type=str, help='rising|falling')
    parser.add_argument('--rtm_translen', default=1234, type=int, help='transient length')
    parser.add_argument('--post', default=100000, type=int, help='shot length')
    parser.add_argument('--trg', default='1,0,1', type=str, help='shot trigger triplet')
    parser.add_argument('--hdmi_slave', default='no', type=str, help='no: use FPTRG, yes: use HDMI trg on d0, full=use all 4 lines')
    parser.add_argument('--es_enable', default=1, type=int, help='0 disables Event Signature')
    parser.add_argument('--trace', default=0, type=int, help='1: enable command trace')
    parser.add_argument('--demux', default=1, type=int, help='0: do not demux')
    parser.add_argument('--config_only', default=0, type=int, help='1: configure RGM, do nothing else')
    parser.add_argument('uuts', nargs='+', help="uut")
    configure_bm(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()
