#!/usr/bin/python
import argparse
import os
import time

import acq400_hapi
from acq400_hapi import netclient as netclient
import socket
import sys

SAMPLESZ = 16

def _run_shot_nc(uut, fn, port):
    os.system('cat {} | pv | nc {} {} 1>/dev/null'.format(fn, uut.uut, port))


def _run_shot_py(uut, fn, port):
    print("_run_shot_py")
    eof = False
    bn = 0
    with open(fn, "rb") as fd:
        with netclient.Netclient(uut.uut, port) as nc:
            while not eof:
                chunk = fd.read(0x100000)
                if len(chunk) == 0:
                    eof = True
                else:
                    nc.sock.send(chunk)
                    sys.stderr.write('\r{}'.format(bn))
                    bn += 1
            nc.sock.shutdown(socket.SHUT_WR)
            sys.stderr.write('\nsocket SHUT_WR, wait for DONE\n')
            while True:
                rx = nc.sock.recv(128)
                if not rx or rx.startswith(b"DONE"):
                    break
            nc.sock.close()
            sys.stderr.write("DONE\n")




_run_shot = _run_shot_nc

def run_shot(uut, shot, fn, port, awgsite):
    print("run_shot {} {}".format(shot, fn))
#    uut.s1.playloop_length = '0 0'
    awgsite.playloop_maxlen = os.stat(fn).st_size/SAMPLESZ
    t1 = time.time()
    _run_shot(uut, fn, port)
    t2 = time.time()
    uut.s0.soft_trigger = '1'
    while awgsite.task_active == '1':
        time.sleep(0.1)
    t3 = time.time()
    return( t1, t2, t3)


def run_test(args):
    global _run_shot
    if args.pure_python:
        _run_shot = _run_shot_py
    port = 54203 if args.overlap_load else 54201
    uut = acq400_hapi.Acq400(args.uut)
    awgsite = uut.svc["s{}".format(args.awgsite)]

    awgsite.shot = '0'
    awgsite.completed_shot = '0'
    times = []
    for shot in range(0, args.reps):
        for fn in args.files:
            times.append(run_shot(uut, shot, fn, port, awgsite))
        if args.gaps:
            time.sleep(args.gaps)

    totalplay = 0
    for shot in times:
        playtime = shot[2] - shot[0]
        totalplay += playtime
        print("{}".format(shot[2] - shot[0]))

    print("mean {}".format(totalplay/len(times)))


def run_main():
    parser = argparse.ArgumentParser(description = 'awg speed test')
    parser.add_argument('--reps', type=int, default=1, help='number of repetitions')
    parser.add_argument('--uut',  default=None, help='uut')
    parser.add_argument('--awgsite', default=1, help="first awg site")
    parser.add_argument('--gaps', default=0, type=int, help='gap in s between shots')
    parser.add_argument('--overlap_load', default=1, type=int)
    parser.add_argument('--pure_python', default=0, type=int)
    parser.add_argument('files', nargs='+', help='files to play')
    run_test(parser.parse_args())

if __name__ == '__main__':
    run_main()

