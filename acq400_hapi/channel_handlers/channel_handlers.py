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

CHDEF,ch_raw[,fmt=F0[;F1,...]]
CHDEF,ch_egu
CHDEF,ch_taiv
CHDEF,ch_bf,MASK[,fmt=l1;l2;l3]

[pgm@hoy5 acq400_hapi]$ cat PCFG/user.pcfg 
# all channels raw:
1,2,8=ch_raw,fmt=AqB1;CNT1;SC
10=ch_bf,0x70000000,fmt=TAIs
10=ch_taiv

# print entire BF
7=ch_bf,0x0000003f,fmt=DI6
# break BF in to bits, lable each bit ..
7=ch_bf,0x0000003f,fmt=d4;d3;d2;d2;d1;d0


'''


STEP = True
SMOO = False


class channel_handler:
    def __init__ (self, ic, fmt):
        self.ic = ic
        self.ch = ic+1
        self.fmt = fmt

    def __call__(self, raw_channels, pses):
        print("ERROR : abstract base class does nothing")

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
        return raw_channels[self.ic][pses[0]:pses[1]:pses[2]], self.fmt.format(self.ch), SMOO

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
        yy, raw_fmt, step = super().__call__(raw_channels, pses)

        if self.args.WSIZE == 4:
            yy = yy/256
        try:
            return self.args.the_uut.chan2volts(self.ch, yy), self.egu_fmt.format(self.ch), SMOO
        except:
            return yy, raw_fmt.format(self.ch), SMOO

    def build(nchan, defstr, client_args):
        channels, args, fmts = channel_handler.defsplit(nchan, defstr, ch_egu.def_fmt)
        if args[0] == 'ch_egu':
            for cn, ch in enumerate(channels):
                channel_handler.handlers.append(
                    ch_egu(ch-1, client_args, fmt=fmts[cn if cn<len(fmts) else 0]))
            return True
        return False

channel_handler.builders.append(ch_egu)

class ch_db(ch_raw):
    def_fmt = "CH{} dB"
    def __init__ (self, ic, args, fmt=None):
        super().__init__(ic)
        _fmt = fmt if fmt else ch_egu.def_fmt
        self.args = args
        self.egu_fmt = _fmt
        self.vmax = 0

    def __call__(self, raw_channels, pses):
        print(np.shape(raw_channels))
        yy, raw_fmt, step = super().__call__(raw_channels, pses)

        dbsq = 10 * np.log10(np.square(yy))
        
        if self.args.WSIZE == 4:
            db0 = 10 * np.log10(7.0368e13)      # 2^23 * 2^23
        else:
            db0 = 10 * np.log10(32768*32768)
        
        return np.subtract(db0, dbsq), self.egu_fmt.format(self.ch), SMOO        

    def build(nchan, defstr, client_args):
        channels, args, fmts = channel_handler.defsplit(nchan, defstr, ch_egu.def_fmt)
        if args[0] == 'ch_db':
            for cn, ch in enumerate(channels):
                channel_handler.handlers.append(
                    ch_db(ch-1, client_args, fmt=fmts[cn if cn<len(fmts) else 0]))
            return True
        return False

channel_handler.builders.append(ch_db)    

class ch_tai_vernier(ch_raw):
    def_fmt = "CH{} TAIv"
    def __init__ (self, ic, args, fmt=None):
        _fmt = fmt if fmt else ch_raw.def_fmt
        super().__init__(ic, _fmt)

        self.args = args

    def __call__(self, raw_channels, pses):
        yy, fmt, step = super().__call__(raw_channels, pses)
        return decode_tai_vernier(self.args, yy), fmt, STEP

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
        self.shr = ch_bitfield.calc_shr(mask)        

    def __call__(self, raw_channels, pses):
        yy = raw_channels[self.ic][pses[0]:pses[1]:pses[2]]
        bf = np.right_shift(np.bitwise_and(yy, self.mask), self.shr)
        return bf, self.fmt.format(self.ch), STEP

    @staticmethod
    def count_bits(mask):
        mask_bits = 0;
        while mask != 0:
            if (mask&1) != 0:
                mask_bits += 1
            mask = mask >> 1
        return mask_bits
    
    @staticmethod
    def calc_shr(mask):
        shr = 0
        while mask&0x1 == 0:
            mask = mask >> 1
            shr += 1
        return shr
    
    def build(nchan, defstr, client_args):
        channels, args, fmts = channel_handler.defsplit(nchan, defstr, ch_bitfield.def_fmt)
        if args[0] == 'ch_bf':
            mask = int(args[1], 16)
            mask_bits = ch_bitfield.count_bits(mask)
            for arg in args:
                if arg.startswith("fmt="):
                    _fmts = arg[4:].split(';')

            if len(channels) == 1 and mask_bits > 1 and len(_fmts) == mask_bits:
                m1 = 1 << (mask_bits + ch_bitfield.calc_shr(mask) - 1)
                for ii in range(0, mask_bits):
                    channel_handler.handlers.append(ch_bitfield(channels[0]-1, m1, fmt=_fmts[ii]))
                    m1 = m1 >> 1
            else:
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

