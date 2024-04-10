import socket
import re

def supported_host(hn_pfx):
    return hn_pfx in ( 'acq1001', 'acq1002', 'acq1102', 'acq2006', 'acq2106', 'acq2206', 'z7io', 'kmcu')

def self_hosted():
    # maybe self-hosted
    hn = socket.gethostname()
    mat = re.compile('([a-z0-9]+)_[0-9]+').match(hn)
    return hn if mat and supported_host(mat.group(1)) else None

