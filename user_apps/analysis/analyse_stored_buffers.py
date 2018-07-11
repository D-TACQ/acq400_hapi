#!/usr/bin/python

# feed a set of filnames from an AFHBA404 capture
# eg 
# find /data/ACQ400DATA/0/acq2106_096/ -type f -name 0.?? | sort -n | ./analyse_stored_buffers.py

# @todo: do this as a subprocess. I failed to get a pipeline to work from python ...

# for each buffer
# report an error if it's NOT in sequence
# for each buffer, compare the last 1K with the last 1K of the same buffer previous cycle
# if it's the SAME (aka buffer overwrite not complete), then report an error.

import subprocess
import sys
import os

verbose = 0
skip = 1
first = True
nb = 99

FNULL = open(os.devnull, 'w')

def nextbuf(ib0):
    return (ib0 + 1) % nb

def compare_files(f0, f1):
    equal = subprocess.call(['cmp', '-i', '4095K', f0, f1], stdout=FNULL, stderr=subprocess.STDOUT) == 0
    if equal:
    	print("cmp {} {} {}".format(f0, f1,  subprocess.call(['cmp', f0, f1])))


#command = "find /data/ACQ400DATA/0/acq2106_096/ -type f | sort -n 
#command = "echo bollocks"
# RULE#1 NEVER user spaces in filenames :-)
#args = command.split(' ')

#proc = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)

ii = 0
ib0 = 0
errcount = 0

while True:
   line = sys.stdin.readline()
   if line == b'':
       break
  
   line = line.rstrip() 
   path = line.split('/')
   icycle = int(path[len(path)-2])
   ibuf = int(path[len(path)-1].split('.')[1])
   if first:
      ib0 = ibuf
      first = False
      continue

   if ibuf != nextbuf(ib0):
       errcount += 1
       print("ERROR: at {} errcount:{}  {} => {}".format(ii, errcount, ib0, ibuf))

   if icycle > 0:
       oldpath = path
       oldpath[len(path)-2] = "{:06d}".format(icycle-1)
       oldf = '/'.join(oldpath)
       compare_files(oldf, line)
   ib0 = ibuf
   if verbose: 
       print("{} {}".format(ii, line.rstrip()))
   ii += 1


