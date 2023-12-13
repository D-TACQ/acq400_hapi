#!/usr/bin/env python3

"""Block until uut has booted

Example::

    ./user_apps/utils/wait_for_ready.py acq2106_123


"""

import urllib.request
import time
import argparse

def wait_ready(args):
    while True:
        try:
            contents = urllib.request.urlopen("http://{}/d-tacq/rc-local-complete".format(args.uut)).read()
            print(contents)
            return True
        except:
            print("{} not ready".format(args.uut))
            time.sleep(2)

def get_parser():
    parser = argparse.ArgumentParser(description='Wait until UUT booted')
    parser.add_argument('uut', nargs=1, help="UUT hostname")
    return parser

# execution starts here
if __name__ == '__main__':
    wait_ready(get_parser().parse_args())



