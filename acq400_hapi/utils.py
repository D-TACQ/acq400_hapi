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
