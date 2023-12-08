#!/usr/bin/env python

"""set GAIN:ALL for sites0"""

import acq400_hapi
import argparse



def set_gain_action(uut, site, gain):
    uut.modules[site].GAIN_ALL = gain

def run_main(args):
    site_list = args.sites.split(',')

    uut = acq400_hapi.factory(args.uut[0])

    for ix, site in enumerate(site_list):
        try:
            gain = args.gains[ix]
        except:
            gain = args.gains[-1]        
        set_gain_action(uut, int(site), gain)

def get_parser():
    parser = argparse.ArgumentParser(description='Set UUT gains')
    parser.add_argument('--sites', type=str, default=1, help="sites to set")
    parser.add_argument('uut', nargs=1, help="uut")
    parser.add_argument('gains', nargs='+', help="gain values in site order")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
