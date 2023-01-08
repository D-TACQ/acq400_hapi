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

CHDEF,ch_raw[,fmt=F0[,F1,...]]
CHDEF,ch_egu
CHDEF,ch_taiv
CHDEF,ch_bf,MASK[,fmt=l1,l2,l3]

[pgm@hoy5 acq400_hapi]$ cat PCFG/user.pcfg 
# all channels raw:
1,2,8=ch_raw,fmt=AqB1,CNT1,SC
10=ch_bf,0x70000000,fmt=TAIs
10=ch_taiv

'''

class channel_handler:
    def __init__ (self, ic, fmt):
        self.ic = ic
        self.ch = ic+1
        self.fmt = fmt

    def __call__(self, raw_channels, pses):
        print("ERRROR : abstract base class does nothing")

    def make_label(self):
        return self.fmt.format(self.ch)

    def defsplit(nchan, defstr, fmt):
        lstr, rstr = defstr.split("=", 1)

        if lstr == 'all' or lstr == ':':
            cdef = list(range(1,nchan+1))
        elif len(lstr.split(':')) > 1:
            lr = lstr.split(':')
            x1 = 1 if lr[0] == '' else int(lr[0])
            x2 = nchan+1 if lr[1] == '' else int(lr[1])+1
            cdef = list(range(x1, x2))
        else:
            cdef = lstr.split(',')
        rlist = rstr.split(',')
        fmts = (fmt,)
        for arg in rlist:
            if arg.startswith("fmt="):
                _fmts = arg[4:].split(';')
                fmts = []
                for cn, ch in enumerate(cdef):
                    fmts.append(fmt if len(_fmts) == 0 else _fmts[0] if cn >= len(_fmts) else _fmts[cn])

        return list(int(xx) for xx in cdef), rlist, fmts
    handlers = []
    builders = []

    def decode_config(nchan, lno, defstr, client_args=None):
        if len(defstr) < 2 or defstr.startswith("#"):
            return
        else:
            for builder in channel_handler.builders:
                if builder.build(nchan, defstr, client_args):
                    return
            print("ERROR: {} no handler found for \"{}\"".format(lno, defstr))


class ch_raw(channel_handler):
    def_fmt = "CH{} bits"

    def __init__ (self, ic, fmt=None):
        _fmt = fmt if fmt else ch_raw.def_fmt
        super().__init__(ic, _fmt)

    def __call__(self, raw_channels, pses):
        return raw_channels[self.ic][pses[0]:pses[1]:pses[2]], self.fmt.format(self.ch)

    def build(nchan, defstr, client_args):
        channels, args, fmts = channel_handler.defsplit(nchan, defstr, ch_raw.def_fmt)
        if args[0] == 'ch_raw':
            for cn, ch in enumerate(channels):
                channel_handler.handlers.append(ch_raw(ch-1, fmt=fmts[cn]))
            return True
        return False

channel_handler.builders.append(ch_raw)


class ch_egu(ch_raw):
    def_fmt = "CH{} V"
    def __init__ (self, ic, args, fmt=None):
        super().__init__(ic)
        _fmt = fmt if fmt else ch_egu.def_fmt
        self.args = args
        self.egu_fmt = _fmt

    def __call__(self, raw_channels, pses):
        print(np.shape(raw_channels))
        yy, raw_fmt = super().__call__(raw_channels, pses)
        try:
            if args.WSIZE == 4:
                yy = yy/256
            return self.args.the_uut.chan2volts(self.ch, yy), self.egu_fmt.format(self.ch)
        except:
            return yy, raw_fmt.format(self.ch)

    def build(nchan, defstr, client_args):
        channels, args, fmts = channel_handler.defsplit(nchan, defstr, ch_egu.def_fmt)
        if args[0] == 'ch_egu':
            for cn, ch in enumerate(channels):
                channel_handler.handlers.append(ch_egu(ch-1, fmt=fmts[cn]))
            return True
        return False

channel_handler.builders.append(ch_raw)


class ch_tai_vernier(ch_raw):
    def_fmt = "CH{} TAIv"
    def __init__ (self, ic, args, fmt=None):
        _fmt = fmt if fmt else ch_raw.def_fmt
        super().__init__(ic, _fmt)

        self.args = args

    def __call__(self, raw_channels, pses):
        yy, fmt = super().__call__(raw_channels, pses)
        return decode_tai_vernier(self.args, yy), fmt

    def build(nchan, defstr, client_args):
        channels, args, fmts = channel_handler.defsplit(nchan, defstr, ch_tai_vernier.def_fmt)
        if args[0] == 'ch_taiv':
            for cn, ch in enumerate(channels):
                channel_handler.handlers.append(ch_tai_vernier(ch-1, client_args, fmt=fmts[cn]))
            return True
        return False

channel_handler.builders.append(ch_tai_vernier)

class ch_bitfield(channel_handler):
    def_fmt = "BITS{}"
    def __init__ (self, ic, mask, fmt=None):
        _fmt = fmt if fmt else ch_bitfield.def_fmt
        super().__init__(ic, fmt)
        self.mask = mask
        self.shr = 0
        while mask&0x1 == 0:
            mask = mask >> 1
            self.shr += 1

    def __call__(self, raw_channels, pses):
        yy = raw_channels[self.ic][pses[0]:pses[1]:pses[2]]
        bf = np.right_shift(np.bitwise_and(yy, self.mask), self.shr)

        return bf, self.fmt.format(self.ch)

    def build(nchan, defstr, client_args):
        channels, args, fmts = channel_handler.defsplit(nchan, defstr, ch_bitfield.def_fmt)
        if args[0] == 'ch_bf':
            mask = int(args[1], 16)
            for cn, ch in enumerate(channels):
                channel_handler.handlers.append(ch_bitfield(ch-1, mask, fmt=fmts[cn]))
            return True
        return False

channel_handler.builders.append(ch_bitfield)

def process_pcfg(args):
    ''' return list of channel_handler objects built from config file '''
    print("process_pcfg {}".format(args.pcfg))
    with open(args.pcfg) as fp:
        for lno, defstr in enumerate(fp.readlines()):
            channel_handler.decode_config(args.nchan, lno, defstr.strip(), client_args=args)
    return channel_handler.handlers

