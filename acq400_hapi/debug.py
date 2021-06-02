'''
Created on 29 Sep 2020

@author: pgm
'''

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Debugger(object):
    """ Debug a method and return it back"""

    enabled = 0

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        if self.enabled:
            logger.debug('{} : {}'.format("Enter" if self.enabled > 2 else "Entering", self.func.__name__))
            logger.debug('args, kwargs : {}'.format(args, kwargs))
            
            if self.enabled > 2:
                inp = input("q/C?")
                if inp == 'q':
                    exit(1)
                    
        rc = self.func(*args, **kwargs)
        
        if self.enabled:
            logger.debug('{} returned : {}'.format(self.func.__name__, rc))
            if self.enabled > 1:
                logger.debug('Exit : {}'.format(self.func.__name__))
                inp = input("q/C?")
                if inp == 'q':
                    exit(1)
            
        return rc
