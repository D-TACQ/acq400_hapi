'''
Created on 19 Jun 2021

@author: pgm
'''

import acq400_hapi
import argparse

def get_parser():
    parser = argparse.ArgumentParser(description='acq400_remote_script') 
    parser.add_argument('-v','--verbose', default=0, help="show more info")
    parser.add_argument('uuts', nargs='+', help="uut[s]")
    return parser
   
def site_model(u, k):
    try:
        if k.startswith('s'):
            return "{},".format(u.svc[k].MODEL)
    except:
        pass

    return ""
         
def run_main(args):
    uuts = [acq400_hapi.factory(u) for u in args.uuts]
    
    for u in uuts:
        sites = "".join([site_model(u, k) for k in sorted(u.svc)]).rstrip(',')
        print("SUCCESS: {} {}".format(u.uut, sites))
    


# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())