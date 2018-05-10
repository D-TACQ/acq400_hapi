#!/usr/bin/env python

""" configure and run gpg on uut
    run_gpg.py [opts] uut
"""

import sys
import acq400_hapi
import argparse
import re


def load_stl(uut, stl):
    with open(stl, 'r') as fp: 
        uut.load_gpg(fp.read(), uut.s0.trace)
        
def make_waterfall(uut, interval, hitime, states):
    stl = ''
    on = True
    cursor = interval
    for s in states:
        if on:
            stl += '%d,%d\n' % (cursor, s)
            on = False
        else:
            stl += '%d,%d\n' % (cursor+hitime, s)
            cursor += interval
            on = True
    uut.load_gpg(stl, uut.s0.trace)
    
def soft_trigger_loop(uut):
    while True:
        key = raw_input("trigger>")
        if key == '':
            uut.s0.soft_trigger = 1
        else:
            break
   
def set_hdmi_master(uut):
    uut.s0.SIG_SYNC_OUT_CLK     = 'CLK'     # CLK d0 output
    uut.s0.SIG_SYNC_OUT_CLK_DX  = 'd0'      # 
    uut.s0.SIG_SYNC_OUT_TRG     = 'TRG'     # SOFT TRIGGER d1
    uut.s0.SIG_SYNC_OUT_TRG_DX  = 'd1'
#    uut.s0.SIG_SYNC_OUT_TRG     = 'GPG'     # trigger from gpg OUT
#    uut.s0.SIG_SYNC_OUT_TRG_DX  = 'd0'
    uut.s0.SIG_SYNC_OUT_SYNC    = 'GPG'     # GPG d1
    uut.s0.SIG_SYNC_OUT_SYNC_DX = 'd1'      # GPG 0x2
    uut.s0.SIG_SYNC_OUT_GPIO    = 'GPG'
    uut.s0.SIG_SYNC_OUT_GPIO_DX = 'd2'      # GPG 0x4

def run_gpg(args):
    uut = acq400_hapi.Acq400(args.uut[0])
 
    
    uut.s0.trace = args.trace
    
    uut.s0.GPG_ENABLE = '0'

    if args.clk == 'notouch':
        print("leave clk untouched") 
    elif args.clk == 'int':
        uut.s0.gpg_clk=0,0,0
    elif args.clk == 'fp':
        uut.s0.SYS_CLK_FPMUX = 'FPCLK'
        uut.s0.gpg_clk='1,0,0'
    else:
        # clk=dX
        uut.s0.gpg_clk='1,{},1'.format(args.clk[1:])
     
    if args.stl != 'none':
        load_stl(uut, args.stl)
    elif args.waterfall != 'none':
        (interval, hitime) = [int(s) for s in re.findall(r'\d+', args.waterfall)]
        make_waterfall(uut, interval, hitime, [1,0,2,0,4,0,8,0])
       
# assume GPG drives 4 lines..
    for dx in [0, 1, 2, 3]:
        uut.s0.set_knob('SIG_EVENT_SRC_{}'.format(dx), 'GPG')
    if args.hdmi_master == 1:
        set_hdmi_master(uut)
    uut.s0.gpg_trg='1,{},1'.format(1 if args.trg.startswith('soft') else 0)
    uut.s0.GPG_MODE=args.mode
    if args.disable != 1:
        uut.s0.GPG_ENABLE = '1'
   
    if args.trg == 'softloop':
        soft_trigger_loop(uut)
    if args.trg == 'softonce':
        uut.s0.soft_trigger = '1'
    
        

def run_main():
    parser = argparse.ArgumentParser(description='run_gpg')    
    parser.add_argument('--trg', default='soft', type=str, help="trigger fp|soft|softloop|softonce")
    parser.add_argument('--clk', default='int', type=str, help='clk int|dX|notouch')
    parser.add_argument('--mode', default='LOOPWAIT', type=str, help='mode')
    parser.add_argument('--disable', default=0, type=int, help='1: disable')
    parser.add_argument('--stl', default='none', type=str, help='stl file')
    parser.add_argument('--waterfall', default='none', help='d0,d1,d2,d3 waterfall [interval,hitime]')
    parser.add_argument('--trace', type=int, default = 0, help='trace wire protocol')
    parser.add_argument('--hdmi_master', type=int, default=0, help='clk, trg and gpg drive HDMI outputs')
    parser.add_argument('uut', nargs=1, help="uut")
    run_gpg(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()
