#!/usr/bin/env python3

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
  --es_enable ES_ENABLE
                        0 disables Event Signature
  --trace TRACE         1: enable command trace
  --demux DEMUX         0: do not demux
"""

import acq400_hapi
import argparse

## configure burst mode. call this if we import the class..
def configure_bm(args, uuts):
    for u in uuts:
        u.s0.GPG_ENABLE = '0'       # needed if running set.burst multiple times
        if args.clear_counters:
            u.clear_counters()          # makes COUNTERS opi easier to read
        u.s1.trg        = args.trg
        u.s1.RGM        = args.rgm
        u.s1.RGM_DX     = args.dx
        u.s1.RGM_SENSE  = args.sense
        u.s1.es_enable  = args.es_enable
        u.s1.RTM_TRANSLEN = args.rtm_translen if args.rgm == 'RTM' else 0
        u.s0.transient  = 'PRE={} POST={} DEMUX={}'.format(args.pre, args.post, args.demux)
        u.s0.set_knob('SIG_SRC_TRG_1', 'GPG1' if args.gpg == 'on' and args.dx == 'd1' else 'STRIG')
    
    uuts[0].s0.SIG_SYNC_OUT_TRG_DX = args.dx 

def run_shot(args, uuts):
    for u in uuts:
        u.s0.set_arm = 1

    for u in uuts:
        u.statmon.wait_armed()

    # warning: this is a RACE for the case of a free-running trigger and multiple UUTs
    if args.gpg == 'on':
        for u in uuts:
            u.s0.GPG_ENABLE = '1'

    if args.trg == '1,1,1':
        for u in uuts:
            u.s0.soft_trigger

def configure_and_run(args, uuts):
    configure_bm(args, uuts)
    if not args.config_only:
        print("running a shot")
        run_shot(args, uuts)


def run_main():
    parser = argparse.ArgumentParser(description='set_burst mode')
    parser.add_argument('--rgm', default='RTM', type=str, help="mode RGM|RTM")
    parser.add_argument('--dx', default='d0', type=str, help='dx d0|d1|d2')
    parser.add_argument('--gpg', default='off', type=str, help='source from gpg on|off')
    parser.add_argument('--sense', default='rising', type=str, help='rising|falling')
    parser.add_argument('--rtm_translen', default=1234, type=int, help='transient length')
    parser.add_argument('--post', default=100000, type=int, help='shot length')
    parser.add_argument('--pre', default=0, type=int, help='pre shot length')
    parser.add_argument('--trg', default='1,0,1', type=str, help='shot trigger triplet')
    parser.add_argument('--es_enable', default=1, type=int, help='0 disables Event Signature')
    parser.add_argument('--demux', default=1, type=int, help='0: do not demux')
    parser.add_argument('--config_only', default=1, type=int, help='1: configure RGM, do nothing else')
    parser.add_argument('--clear_counters', default=0, type=int, help="clear counters (slow)")
    parser.add_argument('uuts', nargs='+', help="uut")
    args = parser.parse_args()
    configure_and_run(args, [acq400_hapi.Acq400(u) for u in args.uuts])

# execution starts here

if __name__ == '__main__':
    run_main()
