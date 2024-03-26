#!/usr/bin/env python3

"""Logging for acq400_hapi"""

import logging
import os

class acq400_logger(logging.getLoggerClass()):
    #https://docs.python.org/3/library/logging.html#logrecord-attributes
    #https://docs.python.org/3/library/time.html#time.strftime
    term_fmt = "[%(levelname)s]: %(message)s"
    file_fmt = "[%(asctime)s %(levelname)s]: %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    formats = {
        logging.DEBUG: {'format': term_fmt},
        logging.INFO: {'format': '%(message)s'},
        logging.WARNING: {'format': term_fmt, 'color': "\x1b[33;20m"},
        logging.ERROR: {'format': term_fmt, 'color': "\x1b[31;20m"},
        logging.CRITICAL: {'format': term_fmt, 'color': "\x1b[31;1m"},
    }

    def __init__(self, name, level=logging.INFO, logfile=None):
        super().__init__(name, level)
        self.setLevel(level)
        self.enable_color = bool(int(os.getenv('HAPI_COLOUR', '1')))
        if logfile:
            fh = logging.FileHandler(logfile)
            fh.setFormatter(self.FileFormatter(self))
            self.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setLevel(level)
        sh.setFormatter(self.Formatter(self))
        self.addHandler(sh)

    def __getattr__(self, name):
        if not hasattr(logging, name.upper()):
            return
        msg_level = getattr(logging, name.upper())
        def wrapper(msg, *args, **kwargs):
            if self.isEnabledFor(msg_level):
                self._log(msg_level, msg, args, **kwargs)
        return wrapper
    
    def add_new_level(self, levelname, levelno, color=None, format=None):
        format = {'format': format} if format else {'format': self.term_fmt} 
        if color: format['color'] = color
        levelname = levelname.upper()
        setattr(logging, levelname, levelno)
        logging.addLevelName(levelno, levelname)
        self.formats[levelno] = format
    

    class BaseFormatter(logging.Formatter):
        def __init__(self, logger):
            super().__init__()
            self.logger = logger
            self.datefmt = self.logger.date_fmt

    class Formatter(BaseFormatter):
        def format(self, record):
            rfmt = self.logger.formats.get(record.levelno)
            style_str = rfmt['format']
            if self.logger.enable_color and 'color' in rfmt:
                reset = '\x1b[0m'
                style_str = f"{rfmt['color']}{style_str}{reset}"
            self._style._fmt = style_str
            return super().format(record)
    
    class FileFormatter(BaseFormatter):
        def format(self, record):
            self._style._fmt = self.logger.file_fmt
            return super().format(record)
        

if __name__ == '__main__':
    log = acq400_logger('acq400_logger', level=logging.DEBUG, logfile='example.log')
    #default log levels
    log.debug('A debug message')
    log.info('A normal message')
    log.warning('A warning')
    log.error('An error has occured')
    log.critical('A CRITICAL error has occured')
    #add custom log level
    log.add_new_level('success', 21, color="\033[92m", format="-={%(levelname)s}=- %(message)s :D")
    log.success('A success has occured')