'''
Created on 13 Dec 2021

@author: pgm
'''

'''
timing on VPN


   set all  ${uut}:${site}:G1_cc
    first, using HAPI. Result on D-TACQVPN for 96 Set, 96 Get:
    [pgm@hoy5 acq400_hapi]$ SITECLIENT_TRACE=1 python ./test_apps/sc32_timing.py acq2106_132
    Siteclient(acq2106_132, 4220) >MODEL
    ...
    Siteclient(acq2106_132, 4221) >SC32:G1:04=0
    Siteclient(acq2106_132, 4221) <
    Siteclient(acq2106_132, 4221) >SC32:G1:05=1
    Siteclient(acq2106_132, 4221) <
    Siteclient(acq2106_132, 4221) >SC32:G1:06=2
    Siteclient(acq2106_132, 4221) <
    Siteclient(acq2106_132, 4221) >SC32:G1:07=3
    Siteclient(acq2106_132, 4221) <
    
    TIMING:func:'set_all_gains' took: 17.08 sec
    get_all_gains (1, 3, 5)
    
    Siteclient(acq2106_132, 4225) >SC32:G1:31
    Siteclient(acq2106_132, 4225) <SC32:G1:31 1000
    Siteclient(acq2106_132, 4225) >SC32:G1:32
    Siteclient(acq2106_132, 4225) <SC32:G1:32 1
    1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1,1,100,1000,1
    TIMING:func:'get_all_gains' took: 16.86 sec
    TIMING:func:'run_test' took: 33.81 sec


timing on LAN:
[dt100@naboo acq400_hapi]$ SITECLIENT_TRACE=1 python3 ./test_apps/sc32_timing.py acq2106_132
...
Siteclient(acq2106_132, 4225) <SC32:G1:30 100
Siteclient(acq2106_132, 4225) >SC32:G1:31
Siteclient(acq2106_132, 4225) <SC32:G1:31 1000
Siteclient(acq2106_132, 4225) >SC32:G1:32
Siteclient(acq2106_132, 4225) <SC32:G1:32 1
10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1
TIMING:func:'get_all_gains' took: 13.37 sec
TIMING:func:'run_test' took: 27.16 sec

timing without debugs:
[dt100@naboo acq400_hapi]$ SITECLIENT_TRACE=0 python3 ./test_apps/sc32_timing.py acq2106_132
set_all_gains (1, 3, 5)
TIMING:func:'set_all_gains' took: 13.29 sec
get_all_gains (1, 3, 5)
10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1
TIMING:func:'get_all_gains' took: 13.87 sec
TIMING:func:'run_test' took: 27.15 sec


=> the cost of the TRACE is zero. The VPN penalty is 6s.


timing on LAN, pure pyepics:
EPICS_CA_ADDR_LIST=acq2106_132 python3 ./test_apps/sc32_timing.py --use_hapi=0 acq2106_132
acq2106_132:5:SC32:G1:28
acq2106_132:5:SC32:G1:29
acq2106_132:5:SC32:G1:30
acq2106_132:5:SC32:G1:31
acq2106_132:5:SC32:G1:32
TIMING:func:'set_all_gains_epics' took: 2.60 sec
get_all_gains_epics (1, 3, 5)
10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1,10,100,1000,1
TIMING:func:'get_all_gains_epics' took: 0.08 sec
TIMING:func:'run_epics_test' took: 2.68 sec

'''

import acq400_hapi
import argparse

try:
    import epics
    use_epics = True
except ModuleNotFoundError as e:
    print(e)
    use_epics = False;

from acq400_hapi import timing as timing


def get_args():
    parser = argparse.ArgumentParser(description = "setting SC32 gains .. timing")
    parser.add_argument('--sites', default='(1,3,5)', help="site [1]")
    parser.add_argument('--use_hapi', default=1, type=int, help="use HAPI to get values")
    parser.add_argument('--use_pyca', default=1, type=int, help="use pyca to get values")
    parser.add_argument('uut', nargs='+', help="uut")
    args = parser.parse_args()
    args.sites = eval(args.sites)
    return args


@timing
def set_all_gains(args, uut):
    G1_GAINS = (1, 10, 100, 1000)
    print("set_all_gains {}".format(args.sites))
    for site in args.sites:
        for ch in range(1,33):
            value = G1_GAINS[ch%4]
            uut.svc["s{}".format(site)].set_knob("SC32_G1_{:02d}".format(ch), value)
            
@timing
def set_all_gains_epics(args):
    G1_GAINS = ('1', '10', '100', '1000')
    print("set_all_gains_epics {}".format(args.sites))
    for site in args.sites:
        for ch in range(1,33):
            pvname = "{}:{}:SC32:G1:{:02d}".format(args.uut[0], site, ch)
            #print(pvname)          
            pv = epics.PV(pvname)
            #value = (ch-1)%4
            value = G1_GAINS[(ch-1)%4]
            pv.put(value, wait=True)

@timing
def get_all_gains(args, uut):
    value = ""
    print("get_all_gains {}".format(args.sites))
    for site in args.sites:
        for ch in range(1,33):
            if len(value):
                value += ","
            value += acq400_hapi.pv(uut.svc["s{}".format(site)].get_knob("SC32_G1_{:02d}".format(ch)))

    print(value)

@timing 
def get_all_gains_epics(args):
    value = ""
    print("get_all_gains_epics {}".format(args.sites))
    for site in args.sites:
        for ch in range(1,33):
            pv = epics.PV("{}:{}:SC32:G1:{:02d}".format(args.uut[0], site, ch))
            if len(value):
                value += ","
            value += str(pv.get())

    print(value)


@timing
def run_test(args, uut):
    set_all_gains(args, uut)
    get_all_gains(args, uut)

@timing
def run_epics_test(args):
    set_all_gains_epics(args)
    get_all_gains_epics(args)
    
def main():
    args = get_args()

    if args.use_pyca and use_epics:
        run_epics_test(args)
    if args.use_hapi:
        uut = acq400_hapi.factory(args.uut[0])
        run_test(args, uut)
    




if __name__ == '__main__':
    main()
