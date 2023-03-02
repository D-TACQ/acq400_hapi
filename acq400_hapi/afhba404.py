'''
Created on 18 Feb 2022

@author: pgm
'''


import subprocess
import os
from collections import namedtuple

def get_connections():
    conns = {}
    p = subprocess.Popen(["get-ident-all", ""], \
             stdout=subprocess.PIPE, stderr=subprocess.PIPE, \
             universal_newlines=True)
    output, errors = p.communicate()
    fields = "host", "dev", "uut", "cx"
    HostComms = namedtuple('HostComms', " ".join(fields))
    for ii, ln in enumerate(output.split('\n')):
        lns = ln.split(' ')
        if len(lns) == 4:
            record = HostComms(**dict(zip(fields, ln.split(' '))))
            conns[ii] = record
    return conns

def get_buffer_len():
    file = "/sys/module/afhba/parameters/buffer_len"
    if os.path.exists(file):
        len = open(file, 'r').read().strip()
        if len.isdigit():
            return int(len)
    return 0

def get_stream_pid(lport):
    file = f"/dev/rtm-t.{lport}.ctrl/streamer_pid"
    if os.path.exists(file):
        pid = open(file, 'r').read().strip()
        if pid.isdigit():
            return int(pid)
    return 0

def get_stream_state(lport):
    file = f"/proc/driver/afhba/afhba.{lport}/Job"
    if os.path.exists(file):
        job_state = open(file, 'r').read().strip()
        states = dict(x.split("=") for x in job_state.split())
        StreamState = namedtuple('StreamState', states)
        return StreamState(**states)
