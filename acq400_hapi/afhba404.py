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

def get_buffer_len(lport):
    file = f"/dev/rtm-t.{lport}.ctrl/buffer_len"
    if os.path.exists(file):
        with open(file, 'r') as f:
            len = f.read().strip()
            if len.isdigit():
                return int(len)
    return 0

def get_stream_pid(lport):
    file = f"/dev/rtm-t.{lport}.ctrl/streamer_pid"
    if os.path.exists(file):
        with open(file, 'r') as f:
            pid = f.read().strip()
            if pid.isdigit():
                return int(pid)
    return 0

def get_state(file, ntname):
    if not os.path.exists(file):
        return None
    with open(file, 'r') as f:
        state_def = f.read().strip().split()
        states = dict((key, int(value)) if value.isdigit() else (key, value) for key,value in (item.split("=") for item in state_def))
        StreamState = namedtuple(ntname, states)
        return StreamState(**states)

def get_stream_state(lport):
    return get_state(f"/proc/driver/afhba/afhba.{lport}/Job", "StreamState")

def get_link_state(lport):
    return get_state(f"/dev/rtm-t.{lport}.ctrl/aurora", "LinkState")

