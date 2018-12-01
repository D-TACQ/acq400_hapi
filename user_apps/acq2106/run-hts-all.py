#!/usr/bin/python

import argparse
import subprocess
import os


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
        except OSError:
            print("OSError, but it's all good")
        args.fifos.append(fn)
            
            

def run_shot(args):
    make_fifos(args)
    cmd = ['mate-terminal']
    tabdef = '--window-with-profile=Default'

    ii = 0
    for uut in args.uuts:
        ports = uuts[uut]
        cmd.append(tabdef)
        cmd.append('--title={}'.format(uut))
        cmd.append('--command=run-hts {} {} {} {}'.\
                format(uut, ports.lport, args.secs, ports.rport))
        tabdef = '--tab-with-profile=Default'
        
        cmd.append(tabdef)
        cmd.append('--title={}.hts'.format(uut))
        cmd.append('--command=cat {}'.format(args.fifos[ii]))                
        ii += 1
    
 

    print(cmd)
    subprocess.check_call(cmd)


def run_main():
    parser = argparse.ArgumentParser(description='run hts all uuts')
    parser.add_argument('--secs', default=100, help='seconds to run')
    parser.add_argument('--etrg', default=0, help='enable external trg TODO')
    parser.add_argument('uuts', nargs='+', help='uut')
    run_shot(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()
