#!/usr/bin/env python

"""
usage: acq400_set_gain.py --site [sitelist] UUT gain

set GAIN:ALL for sites0

positional arguments:
  uut         uut  restart|stop

optional arguments:
  -h, --help  show this help message and exit
"""

import acq400_hapi
import argparse



def set_gain_action(uut, site, gain):
    uut.modules[site].GAIN_ALL = gain
    
 
      
parser = argparse.ArgumentParser(description='configure site gains')
parser.add_argument('--sites', type=str, default=1, help="sites to set")
parser.add_argument('uut', nargs=1, help="uut")
parser.add_argument('gains', nargs='+', help="gain values in site order")

args = parser.parse_args()

site_list = args.sites.split(',')

uut = acq400_hapi.factory(args.uut[0])

for ix, site in enumerate(site_list):
    try:
        gain = args.gains[ix]
    except:
        gain = args.gains[-1]        
    set_gain_action(uut, int(site), gain)
