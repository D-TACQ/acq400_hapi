#!/usr/bin/env python3

import acq400_hapi
import subprocess
import time

UUT='acq2206_017'
PGSITE = 3
TOP='acq1001_594'
MAXSHOTS=10


def run_main():
    uut = acq400_hapi.factory(UUT)
    top = acq400_hapi.factory(TOP)

    for ii in range(0, MAXSHOTS):
        print('-'*80)
        print(f'SHOT={ii}')
        top_result = subprocess.Popen(['./user_apps/acq1001/run_livetop.py', TOP], stdout=subprocess.PIPE, text=True)
        while acq400_hapi.pv(top.s0.CONTINUOUS_STATE) != "ARM":
            time.sleep(1)

        pgsvc = uut.svc[f's{PGSITE}']
        pgsvc.GPG_ENABLE = '0'
        time.sleep(1)
        pgsvc.GPG_ENABLE = '1'
        time.sleep(1)
        uut.s0.soft_trigger = '1'
        time.sleep(1)
        output, error = top_result.communicate()
        print(output)
        time.sleep(2)


# execution starts here

if __name__ == '__main__':
    run_main()


