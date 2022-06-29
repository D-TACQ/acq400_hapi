#!/usr/bin/env python
# recreate Mustang tail light pattern on HFBRPANEL-16.

'''
./user_apps/TIGA/mustang_stl.py --indicator=hazard >STL/mustang-v8-hazard.stl
./user_apps/TIGA/mustang_stl.py --indicator=left >STL/mustang-v8-left.stl
./user_apps/TIGA/mustang_stl.py --indicator=right >STL/mustang-v8-right.stl
'''

import acq400_hapi
import os
import argparse
import sys
import copy


def get_args():
    parser = argparse.ArgumentParser(description='pg_test')
    parser.add_argument('--flat', default=2, type=int, help="dwell ticks per state")
    parser.add_argument('--indicator', default='hazard', help="chose hazard, left, right")
    args = parser.parse_args()
    return args
    
def mustang(args):
    start_pattern_lr = [ 
                0x1 if args.indicator == 'left' or args.indicator == 'hazard' else 0x80,
                0x80  if args.indicator == 'right' or args.indicator == 'hazard' else 0x01
              ]
    
    pattern = copy.deepcopy(start_pattern_lr)
    tick = 0
    
    print("{:3d},0x{:04x}".format(tick, pattern[0]<<8|pattern[1]))
    for st in range(0, 7):        
        for lr in range(0, 2):
            if start_pattern_lr[lr] == 0x1:                
                pattern[lr] = pattern[lr] << 1
            else:
                pattern[lr] = pattern[lr] >> 1
        tick += args.flat
        print("{:3d},0x{:04x}".format(tick, pattern[0]<<8|pattern[1]))
    
    tick += args.flat
    print("{:3d},0x{:04x}".format(tick, start_pattern_lr[0]<<8|start_pattern_lr[1]))       
    

    
    
def main():
    mustang(get_args())

if __name__ == '__main__':
    main()
