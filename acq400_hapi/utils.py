'''
Created on 11 Jul 2021

@author: pgm
'''

import time
from functools import wraps

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print('TIMING:func:%r took: %2.2f sec' % (f.__name__, te-ts))
        return result
    return wrap

def timing_ms(f):
    @wraps(f)
    def wrap(*args, **kw):
        v1 = None
        v2 = None
        for arg in args:
            if v1 is None:
                v1 = arg
            elif v2 is None:
                v2 = arg
            else:
                v2 = v2 + ',' + arg

        ts = time.time()
        result = f(*args, **kw)
        ms = (time.time() - ts) * 1000
        print('func:%6.1f ms %r %s' % (ms, f.__name__, v2))
        return result
    return wrap

class DotDict(dict):
    __delattr__ = dict.__delitem__
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

class Tri(str):
    """Helper class for Trinarys"""
    enum = ['enabled', 'source', 'sense']
    def __new__(cls, value):
        value = ",".join(map(str, value)) if isinstance(value, list) else value
        return super().__new__(cls, value)
    
    def __getitem__(self, key):
        return int(self.split(',')[key])

    def __getattr__ (self, attr):
        if attr in self.enum: return int(self[self.enum.index(attr)])
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {attr!r}")
    
    def mask(self, name, value):
        arr = list(self.split(','))
        arr[self.enum.index(name)] = str(value)
        return ','.join(arr)


def extract_key_values(string):
    return {k: v for k, v in (item.split('=', 1) for item in string.split())}