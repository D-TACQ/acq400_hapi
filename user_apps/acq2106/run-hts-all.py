#!/usr/bin/python

import argparse
import subprocess
import os
import sys
import time

import acq400_hapi

class Struct(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

def map_uuts():
    ids = subprocess.check_output(["get-ident-all"]).split('\n')
    uut_port_map = {}
    maps = [ id.split(' ') for id in ids ]
    for map in maps:
        if len(map) == 4 and map[2].startswith('acq2106'):
            s = Struct(uut=map[2], lport=map[1], rport=map[3])
            uut_port_map[s.uut] = s

    return uut_port_map

uuts = map_uuts()


def make_fifos(args):
    args.fifos = []
    for uut in args.uuts:
        fn = "/tmp/{}.hts".format(uut)
        try:
            os.mkfifo(fn)            
        except OSError, e:
            if e.errno != 17:            
                sys.exit("ERORR OSError, {}", e)
                
        args.fifos.append(fn)
            
scmd = ('python', '-u', './user_apps/acq400/sync_role.py')

def set_sync_roles(args):
    print("set_sync_roles")
    # --toprole=master,fptrg --fclk=10M --enable_trigger=1 $UUTS
    cmd = []
    cmd.extend(scmd)
    toprole = 'master'
    if args.etrg == 1:
        toprole += ',fptrg'
    cmd.append('--toprole={}'.format(toprole))
    cmd.append('--fclk=10M')
    for uut in args.uuts:
        cmd.append(uut)
    print(cmd)
    subprocess.check_call(cmd)        

def wait_for_arm(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]
    
    for uut in uuts:
        while uut.s0.CONTINUOUS_STATE.split(' ')[1] != 'ARM':
            print("polling {} for ARM".format(uut.uut))
            time.sleep(1)
            
def release_the_trigger(args):
    wait_for_arm(args)
    print("RELEASE the trigger REMOVEME when hardware fixed")
    cmd = []
    cmd.extend(scmd)
    cmd.append('--enable_trigger=1')
    cmd.append(args.uuts[0])
    print(cmd)
    subprocess.check_call(cmd)     

def run_shot(args):
    make_fifos(args)
    set_sync_roles(args)
    cmd = ['mate-terminal']
    tabdef = '--window-with-profile=Default'

    for ii, uut in enumerate(args.uuts):
        ports = uuts[uut]
        cmd.append(tabdef)
        cmd.append('--title={}'.format(uut))
        cmd.append('--command=run-hts {} {} {} {}'.\
                format(uut, ports.lport, args.secs, ports.rport))
        tabdef = '--tab-with-profile=Default'
        
        cmd.append(tabdef)
        cmd.append('--title={}.hts'.format(uut))
        cmd.append('--command=cat {}'.format(args.fifos[ii]))                

    print(cmd)
    subprocess.check_call(cmd)

    if args.etrg == 1:
       release_the_trigger(args) 

def run_main():
    parser = argparse.ArgumentParser(description='run hts all uuts')
    parser.add_argument('--secs', default=100, help='seconds to run')
    parser.add_argument('--etrg', type=int, default=0, help='enable external trg TODO')
    parser.add_argument('uuts', nargs='+', help='uut')
    run_shot(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()
