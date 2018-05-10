#!/usr/bin/env python
# run a livetop process
import acq400_hapi
import argparse

def run_shot(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    acq400_hapi.cleanup.init()
    uut.run_livetop()
    
def run_main():
    parser = argparse.ArgumentParser(description='acq1001 livetop demo')
    parser.add_argument('uuts', nargs=1, help="uut ")
    run_shot(parser.parse_args())    

# execution starts here

if __name__ == '__main__':
    run_main()


