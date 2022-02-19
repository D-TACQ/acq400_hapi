'''
Created on 18 Feb 2022

@author: pgm
'''


import subprocess
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

