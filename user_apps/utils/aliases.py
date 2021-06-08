#!/usr/bin/env python
# print apparent positions of aliases in spectrum. Assume F0 is sub-nyquist

import sys

FS = 1e6 if len(sys.argv) < 2 else float(sys.argv[1])
FN = FS/2
F0 = 100e3 if len(sys.argv) < 3 else float(sys.argv[2])

print("aliases FS {} NY {} F0 {}".format(FS, FN, F0))

fcursor = F0

for h in range(0, 10):
    fh = (h+1)*F0
    wraps = int(fh // FN)
    residue = fh - wraps*FN
    if wraps&1:
        hbin = FN-residue
    else:
        hbin = residue
    print("F{} {:.2e} appears at {:.2e} wraps {}".format(h, fh, hbin, wraps))


    


