#!/usr/bin/python
import argparse
import time
import epics
import socket
import re

def play_pattern(args):
    uut = args.uut
    site = args.site

    print(f'play_pattern() {uut}:{site}')

    dio_mode = epics.PV(f"{uut}:{site}:DIO:MODE").get(as_string=True)
    print(dio_mode)
    if dio_mode != 'IMM':
        print("WARNING: DIO not in IMMediate mode, abort")
        return -1


    eight_bits = [epics.PV(f"{uut}:{site}:IMM:DO:BYTE1.B{b}") for b in range(0, 8)]

    while True:
        print('.', end='', flush=True)

        for b in range(0, len(eight_bits)):
            eight_bits[b].put(1, wait=True)
            time.sleep(0.1)
            eight_bits[b].put(0, wait=True)


def run_main(args):
    if args.uut is not None:
        if args.site is not None:
            play_pattern(args)
            return 0
        else:
            print("ERROR: please specify site for DIO482 in {args.uut}")
    else:
        # maybe self-hosted
        hn = socket.gethostname()

        if re.compile('acq[0-9]+_[0-9]+').match(hn):
            sitelist = epics.PV(f'{hn}:SITELIST').get()
            pat = re.compile('([0-9])=dio')
            for tok in sitelist.split(','):
                mat = pat.match(tok)
                if mat:
                    args.uut = hn
                    args.site = mat.group(1)
                    play_pattern(args)
                    return 0

    print("no way today")
    return -1

def get_parser():
    parser = argparse.ArgumentParser(description='dio_immediate_pattern: play a continuous walking bit pattern')
    parser.add_argument('--site', default=None, help="site of DIO482")
    parser.add_argument('uut', default=None, nargs='?', help="uut")
    return parser
if __name__ == '__main__':
	run_main(get_parser().parse_args())
