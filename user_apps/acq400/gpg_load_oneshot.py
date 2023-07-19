#!/usr/bin/env python3

''' gpg_load_oneshot [--stl stl] [acq400_upload opts] uut [uut2] ...

Configure uut for Burst RGM operation, with bursts self-stimulated from the Gate Pulse Generator GPG.

This program makes initial customisation:
    set_rgm(): configures Burst RGM
    set_gpg(): configures Gate Pulse Generator GPG

Example usage:

 NETCLIENT_TRACE=1 SITECLIENT_TRACE=1 ./user_apps/acq400/gpg_load_oneshot.py \
    --capture=1 --remote_trigger=EXT --pre=0 --post=4000000 \
    --stl ./STL/4x2Hz.stl \ 
    --es_enable=0 \
    --channels=1,2 --plot_data=-2 \
    acq2106_178
    
ref: acq2106-gpg-acq48x-fat-r2

START trigger is supplied ONCE on FP TRG (TRG.d0)
GPG provides BURST pulses on EVT.d0 to both ADC system and output on AUX2

'''

import acq400_hapi
import argparse
import acq400_fullshot
        
def get_stl(stl):
    with open (stl, "r") as stl_file:
        stl = stl_file.read()
    return stl

def set_gpg(args, uut):
    uut.s0.gpg_enable = 0
#    uut.s0.GPG_TRG = 'external'
#    uut.s0.GPG_TRG_DX = 'd0'
#    uut.s0.GPG_TRG_SENSE = 'rising'
    uut.s0.GPG_MODE = 'LOOPWAIT'
    uut.s0.gpg_trg = '1,0,1'
    stl = get_stl(args.stl)
    uut.load_gpg(stl)    
    uut.s0.gpg_enable = 1
    
    uut.s0.SIG_EVENT_SRC_0 = 'GPG'
    uut.s0.SIG_FP_GPIO = 'EVT0'
        
def set_rgm(args, uut):
    uut.s1.RGM = 'RGM'
    uut.s1.RGM_DX = 'd0'
    uut.s1.RGM_SENSE = 'rising'
    if args.es_enable is not None:
        uut.s1.es_enable = args.es_enable

def main(args):
    uuts = [ acq400_hapi.factory(u) for u in args.uuts ]    

    for uut in uuts:
        set_rgm(args, uut)
        set_gpg(args, uut)

    acq400_fullshot.run_main(args)
    
def get_parser():
    parser = acq400_fullshot.get_parser()    
    parser.add_argument('--stl', default='./test.stl', type=str, help="GPG pulse pattern STL") 
    parser.add_argument('--es_enable', default=None, help="enable/disable Event Signature (default: no touch)")
    return parser

if __name__ == '__main__':
    main(get_parser().parse_args())


