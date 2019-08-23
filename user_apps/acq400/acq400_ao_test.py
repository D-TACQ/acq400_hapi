#!/usr/bin/env python

"""
Displays a pattern on the first 8 AO channels in order to see them on CS Studio.
"""

import acq400_hapi
import numpy as np
import argparse
import time


def set_ident(uut):
    for ch in list(range(1,9)):
        # return to ident pattern
        exec('uut.s5.AO_{:>02} = {}'.format(ch, ch*2048))


def main():
    parser = argparse.ArgumentParser(description='AO test')
    parser.add_argument('uut', nargs='+', help="uuts")
    args = parser.parse_args()

    uut = acq400_hapi.Acq400(args.uut[0])
    set_ident(uut)

    while True:
        uut.s5.AO_01 = 0
        uut.s5.AO_08 = 16384
        for ch in list(range(2,8)):
            for dc_voltage in list(range(100, 16000, 1000)):
                exec('uut.s5.AO_{:>02} = {}'.format(ch, dc_voltage))
                print("Looped")
                time.sleep(1)

            set_ident(uut)



if __name__ == '__main__':
    main()
