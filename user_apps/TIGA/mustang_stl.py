#!/usr/bin/env python
# recreate Mustang tail light pattern on HFBRPANEL-16.

'''
./user_apps/TIGA/mustang_stl.py --indicator=hazard >STL/mustang-v8-hazard.stl
./user_apps/TIGA/mustang_stl.py --indicator=left >STL/mustang-v8-left.stl
./user_apps/TIGA/mustang_stl.py --indicator=right >STL/mustang-v8-right.stl
./user_apps/TIGA/mustang_stl.py --indicator=follow >STL/mustang-v8-follow.stl
'''

import acq400_hapi
import os
import argparse
import sys
import copy


def get_args():
    parser = argparse.ArgumentParser(description='pg_test')
    parser.add_argument('--flat', default=2, type=int, help="dwell ticks per state")
    parser.add_argument('--indicator', default='hazard', help="chose hazard, left, right, follow")
    args = parser.parse_args()
    return args
    
def mustang(args):
    start_patterns = {
        # bits number R->L, but channels on HFBR panel numbered L->R
        'follow': [ 0x80, 0x01 ],
        'right' : [ 0x01, 0x01 ],   # bit shifts L but lamps shift R
        'left'  : [ 0x80, 0x80 ],
        'hazard': [ 0x01, 0x80 ]
    }
    start_pattern_lr = start_patterns[args.indicator] 
    
    pattern = copy.deepcopy(start_pattern_lr)
    tick = 0
    
    print("{:3d},0x{:04x}".format(tick, pattern[0]|pattern[1]<<8))
    for st in range(0, 7):        
        for lr in range(0, 2):
            if start_pattern_lr[lr] == 0x1:                
                pattern[lr] = pattern[lr] << 1
            else:
                pattern[lr] = pattern[lr] >> 1
        tick += args.flat
        print("{:3d},0x{:04x}".format(tick, pattern[0]|pattern[1]<<8))
    
    tick += args.flat
    print("{:3d},0x{:04x}".format(tick, start_pattern_lr[0]|start_pattern_lr[1]<<8))       
    

    
    
def main():
    mustang(get_args())

if __name__ == '__main__':
    main()
