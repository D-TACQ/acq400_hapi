#!/usr/bin/python
"""
UUT provides a single sample of mean data on 42100, thanks to this 

acq1001_343> cat /mnt/local/inetd.mean.conf 
42100 stream tcp nowait root cat cat /dev/shm/subrate
42100 dgram udp wait root cat cat /dev/shm/subrate

acq1001_343> inetd /mnt/local/inetd.mean.conf



Tested on ACQ1001+ACQ435, buffer length  4096, SR=10000

acq1001_343> cat /mnt/local/sysconfig/acq400.sh 
REBOOT_KNOB=y
BLEN=4096

Buffer Samples: 4096/4/32 = 32 

Buffer Rate = 10000/32 = 330Hz

/dev/shm/subrate is updated at Buffer Rate.


Client side tests:

[dt100@brotto acq400]$ time  ./mean_client.py --verbose=0 --maxsam=100 acq1001_343

real	0m0.974s

ie 100 values per second is possible.

[dt100@brotto acq400]$  ./mean_client.py --maxsam=10 acq1001_343 | cut -d, -f1-8
000004a6,fffff93c,00000898,fffffc3d,00000bf3,fffffa4d,00000f8b,ffffec1c
000002e5,fffff936,00000895,fffffc5c,00000c00,fffffa44,00000fa0,ffffec22
00000c14,fffff95a,0000086a,fffffc45,00000c1e,fffffa31,00000fb2,ffffec10
00000304,fffff933,0000089a,fffffc55,00000c01,fffffa53,00000fca,ffffec1a
00000496,fffff942,00000882,fffffc45,00000c3d,fffffa31,00000fcb,ffffec05
00000933,fffff941,00000894,fffffc44,00000c22,fffffa5b,00000fac,ffffec2f
000003f1,fffff97f,0000089b,fffffc46,00000bfe,fffffa4a,00000f9b,ffffec25
00000a8d,fffff964,0000087a,fffffc61,00000c27,fffffa61,00000f9b,ffffec1a
00000386,fffff967,00000873,fffffc42,00000c18,fffffa46,00000fc8,ffffec3f

Mean values are int32.

"""


import acq400_hapi
import sys
import subprocess
import argparse

MEANPORT = 42100

def get_mean(args):
    uut = args.uut[0]
    sample_size = args.nchan * 4
    
    isam = 0
    while isam < args.maxsam:
        nc = acq400_hapi.Netclient(uut, MEANPORT)
        sample = nc.sock.recv(sample_size)
        if len(sample) != sample_size:
#            sys.stderr.write("short return {}".format(len(sample)))
             continue
        else:
            isam += 1
            if args.verbose:
	        sproc = subprocess.Popen(['hexdump', '-ve', '32/4 "%08x," "\\n"'], stdin=subprocess.PIPE)
                sproc.stdin.write(sample)
                sproc.stdin.close()


parser = argparse.ArgumentParser(description='configure acq400_abort')
parser.add_argument('--maxsam', type=int, default=1, help="number of samples to collect")
parser.add_argument('--nchan', type=int, default=32, help="number of channels per sample")
parser.add_argument('--verbose', type=int, default=1, help="1: dump data, 0: silent")
parser.add_argument('uut', nargs='+', help="uut")
get_mean(parser.parse_args())

    
