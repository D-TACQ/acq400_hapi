# channel_handlers.py

''' channel_handlers will take care of a specific column in a 2D data set, with user-specified formatting
'''


import numpy as np


def decode_tai_vernier(args, y):
    xdt = 25e-9 if args.xdt == 0 else args.xdt
    secs = np.right_shift(np.bitwise_and(y, 0x70000000), 28)
# secs has a spike on rollover, suppress it
    for ii in range(1,len(secs)-1):
        if secs[ii-1] == secs[ii+1] and secs[ii] != secs[ii-1]:
            print("ted fix at {}".format(ii))
            secs[ii] = secs[ii-1]
    ticks = np.bitwise_and(y, 0x0fffffff)*xdt

# catch ticks only spike
    for ii in range(1,len(ticks)-1):
        if ticks[ii] < ticks[ii-1] and ticks[ii+1] > ticks[ii-1]:
            ticks[ii] = (ticks[ii+1]+ticks[ii-1])/2
        elif ticks[ii] > ticks[ii+1] and ticks[ii+1] > ticks[ii-1]:
            ticks[ii] = (ticks[ii+1]+ticks[ii-1])/2

    secs = secs + ticks
    print("decode_tai_vernier @@todoi stubbed spikes")
    return secs

''' formatfile

CHDEF ::
   N : channel number from 1
   LIST : list of channels   eg 1,2,3
   RANGE: range of channels 1:4,   : means ALL
   
CHDEF,raw[,fmt=F]
CHDEF,egu
CHDEF,tai
CHDEF,bf,MASK
'''

class channel_handler:
    def __init__ (self, ic, fmt):
        self.ic = ic
        self.ch = ic+1
        self.fmt = fmt
    def __call__(self, raw_channels, pses):
        print("ERRROR : abstract base class does nothing")
        
    def defsplit(nchan, defstr):
        lstr, rstr = defstr.split("=")
        
        if lstr == 'all' or lstr == ':':
            cdef = list(range(1,nchan+1))
        elif len(lstr.split(':')) > 1:
            lr = lstr.split(':')
            x1 = 1 if lr[0] == '' else int(lr[0])
            x2 = nchan+1 if lr[1] == '' else int(lr[1])+1
            cdef = list(range(x1, x2))
        else:
            cdef = lstr.split(',')
        return list(int(xx) for xx in cdef), rstr.split(',')
    handlers = []
    builders = []
    
    def decode_config(nchan, lno, defstr):
        if len(defstr) < 2 or defstr.startswith("#"):
            return
        else:
            for builder in channel_handler.builders:
                if builder.build(nchan, defstr):
                    return 
            print("ERROR: {} no handler found for \"{}\"".format(lno, defstr))
        

class ch_raw(channel_handler):
    def __init__ (self, ic, fmt = "CH{} bits"):
        super().__init__(ic, fmt)

    def __call__(self, raw_channels, pses):
        return raw_channels[self.ic][pses[0]:pses[1]:pses[2]], self.fmt.format(self.ch)
    
    def build(nchan, defstr):
        channels, args = channel_handler.defsplit(nchan, defstr)
        if args[0] == 'ch_raw':
            for ch in channels:
                channel_handler.handlers.append(ch_raw(ch-1))
            return True
        return False
   
channel_handler.builders.append(ch_raw)         


class ch_egu(ch_raw):
    def __init__ (self, ic, args, fmt="CH{} V"):
        super().__init__(ic)
        self.args = args
        self.egu_fmt = fmt

    def __call__(self, raw_channels, pses):
        print(np.shape(raw_channels))
        yy, raw_fmt = super().__call__(raw_channels, pses)
        try:
            if args.WSIZE == 4:
                yy = yy/256
            return self.args.the_uut.chan2volts(self.ch, yy), self.egu_fmt.format(self.ch)
        except:
            return yy, raw_fmt.format(self.ch)

            yy = decode_tai_vernier(args, yy)            

class ch_tai_vernier(ch_raw):
    def __init__ (self, ic, args, fmt = "CH{} TAIv"):
        super().__init__(ic, fmt)
        self.args = args

    def __call__(self, raw_channels, pses):
        yy, fmt = super.__call__(raw_channels, pses)
        return decode_tai_vernier(self.args, yy), fmt


def process_pcfg(args):
    ''' return list of channel_handler objects built from config file '''
    print("process_pcfg {}".format(args.pcfg))
    with open(args.pcfg) as fp:
        for lno, defstr in enumerate(fp.readlines()):
            channel_handler.decode_config(args.nchan, lno, defstr.strip())
    return channel_handler.handlers

