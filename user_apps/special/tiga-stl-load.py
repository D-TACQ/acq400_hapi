#!/usr/bin/env/python3

import acq400_hapi
import argparse


def get_parser():
    parser = argparse.ArgumentParser(description='TIGA stl load.')
    parser.add_argument('--stl', default='./wd.stl', type=str, help="Which STL file to load")
    parser.add_argument('--ts', default=50000, type=int, help="GPG TimeScaler")
    parser.add_argument('uuts', nargs='+', help="Names of uuts to test.")
    return parser


def get_stl(stl):
    with open (stl, "r") as stl_file:
        stl = stl_file.read()
    return stl


def load_stl(uuts, stl, ts):
    uuts = [ acq400_hapi.Acq2106_TIGA(uut) for uut in uuts ]
    for uut in uuts:
        for site in [2,3,4,5]:
            uut.modules[site].gpg_enable = 0
            uut.modules[site].gpg_timescaler = ts
            uut.load_dio482pg(site, stl, trace=1)
            uut.modules[site].gpg_mode = "ONCE"
            uut.modules[site].gpg_enable = 1

    return None


def main(args):
    stl = get_stl(args.stl)
    load_stl(args.uuts, stl, args.ts)

if __name__ == '__main__':
    main(get_parser().parse_args())
