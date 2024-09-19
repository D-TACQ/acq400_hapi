#!/usr/bin/env python3
SITES=6

LABELS=('MAG', 'PHI', 'PWR')

MAXCHAN=SITES*8*3

print('{:4} {:4} {:4} {}'.format("OFF", "CH", "FOIL", "FUNC"))
for ch in range(1, MAXCHAN+1):
    off=ch-1
    print(f'{off:4} {ch:4} {off//3+1:4} {LABELS[off%3]}')


