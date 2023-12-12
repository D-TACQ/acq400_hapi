#!/usr/bin/python


import numpy as np
import argparse
import acq400_hapi


def load_dpg(args):
    uut = acq400_hapi.Acq400(args.uut[0])

    with open (args.file, "r") as stl_file:
        stl = stl_file.read()
    print(stl)

    uut.load_dpg(stl)
    return None

def get_parser():
    parser = argparse.ArgumentParser(description='simple dpg demo')
    acq400_hapi.Acq400UI.add_args(parser, post=False, pre=False)
    parser.add_argument('--file', default="", help="file to load")
    parser.add_argument('uut', nargs=1, help="uut ")
    return parser

if __name__ == '__main__':
    load_dpg(get_parser().parse_args())


