#!/usr/bin/env python


import argparse
import json
import acq400_hapi


def get_args():

    parser = argparse.ArgumentParser(description="json load test")
    acq400_hapi.Acq400UI.add_args(parser, transient=False, uuts=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    print(args.uuts)
    return None


if __name__ == '__main__':
    main()
