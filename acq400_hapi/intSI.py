

class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

DEC = AttributeDict({ 'k': 1000, 'M': 1000000, 'G': 1000000000 })
BIN = AttributeDict({ 'k': 0x400, 'M': 0x100000, 'G': 0x40000000 })
