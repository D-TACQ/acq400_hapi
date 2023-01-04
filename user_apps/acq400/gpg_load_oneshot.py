#!/usr/bin/env python3

import acq400_hapi
import argparse
import acq400_upload
        
def get_stl(stl):
    with open (stl, "r") as stl_file:
        stl = stl_file.read()
    return stl

def set_gpg(args, uut):
    uut.s0.gpg_enable = 0
    uut.s0.GPG_TRG = 'external'
    uut.s0.GPG_TRG_DX = 'd0'
    uut.s0.GPG_TRG_SENSE = 'rising'
    uut.s0.GPG_MODE = 'LOOPWAIT'
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

    acq400_upload.run_main(args)
    
def get_args():
    parser = acq400_upload.get_args()    
    parser.add_argument('--stl', default='./test.stl', type=str, help="GPG pulse pattern STL") 
    parser.add_argument('--es_enable', default=None, help="enable/disable Event Signature (default: no touch)")
    return parser

if __name__ == '__main__':
    main(get_args().parse_args())


