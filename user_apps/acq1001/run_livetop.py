#!/usr/bin/env python
"""
run a livetop process

usage: run_gpg.py [-h] [--trg TRG] [--clk CLK] [--mode MODE]
                  [--disable DISABLE] [--stl STL] [--waterfall WATERFALL]
                  [--trace TRACE] [--hdmi_master HDMI_MASTER]
                  uut

run_gpg

positional arguments:
  uut                   uut

optional arguments:
  -h, --help            show this help message and exit
  --trg TRG             trigger fp|soft|softloop|softonce
  --clk CLK             clk int|dX|notouch
  --mode MODE           mode
  --disable DISABLE     1: disable
  --stl STL             stl file
  --waterfall WATERFALL
                        d0,d1,d2,d3 waterfall [interval,hitime]
  --trace TRACE         trace wire protocol
  --hdmi_master HDMI_MASTER
                        clk, trg and gpg drive HDMI outputs
"""


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


