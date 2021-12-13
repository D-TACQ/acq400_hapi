'''
Created on 13 Dec 2021

@author: pgm
'''

import acq400_hapi
import argparse

from acq400_hapi import timing as timing


def get_args():
    parser = argparse.ArgumentParser(description = "setting SC32 gains .. timing")
    parser.add_argument('--sites', default='(1,3,5)', help="site [1]")
    parser.add_argument('uut', nargs='+', help="uut")
    args = parser.parse_args()
    args.sites = eval(args.sites)
    return args


@timing
def set_all_gains(args, uut):
    G1_GAINS = (1, 10, 100, 1000)
    print("set_all_gains {}".format(args.sites))
    for site in args.sites:
        for ch in range(1,33):
            value = G1_GAINS[ch%4]
            uut.svc["s{}".format(site)].set_knob("SC32_G1_{:02d}".format(ch), value)

@timing
def get_all_gains(args, uut):
    value = ""
    print("get_all_gains {}".format(args.sites))
    for site in args.sites:
        for ch in range(1,33):
            if len(value):
                value += ","
            value += acq400_hapi.pv(uut.svc["s{}".format(site)].get_knob("SC32_G1_{:02d}".format(ch)))

    print(value)

@timing
def run_test(args, uut):
    set_all_gains(args, uut)
    get_all_gains(args, uut)
    
def main():
    args = get_args()
    
    uut = acq400_hapi.factory(args.uut[0])
    run_test(args, uut)



if __name__ == '__main__':
    main()
