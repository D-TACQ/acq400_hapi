'''
Created on 29 Sep 2020

@author: pgm
'''

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

class Debugger(object):
    """ Debug a method and return it back"""

    enabled = 0
    stack_level = 0

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        if Debugger.enabled:
            Debugger.stack_level += 1            
            logger.debug('{} {} {} {}'.format("===>" * self.stack_level, "Enter" if Debugger.enabled > 2 else "Entering", self.func.__name__, args, kwargs))
            
            if Debugger.enabled > 2:
                inp = input("Enter {}() q/C?".format(self.func.__name__))
                if inp == 'q':
                    exit(1)
                    
        rc = self.func(*args, **kwargs)
        
        if Debugger.enabled:
            logger.debug('{} returned : {}'.format(self.func.__name__, rc))
            if self.enabled > 1:
                logger.debug('Exit : {}'.format(self.func.__name__))
                inp = input("Exit {}() q/C?".format(self.func.__name__))
                if inp == 'q':
                    exit(1)
            Debugger.stack_level = Debugger.stack_level - 1
            
        return rc
