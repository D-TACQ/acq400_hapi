#!/usr/bin/env python
# burst tester for single column, 16 bit burst data


import numpy as np
import matplotlib.pyplot as plt

BL=20224
FN='shot1'

print(f'test if file {FN} is a single channel int16 with burst length {BL}')

with open(FN, 'rb') as bf:
    raw = bf.read()

ushorts = np.frombuffer(raw, dtype=np.uint16)

bc = len(ushorts)//BL

ubursts = ushorts.reshape(bc, BL)

es = ubursts[:,0]
esmagic = es[0]

print(f'esmagic: {esmagic:04x}')

assert (es == esmagic).all() == True

for e in es:
    print(f'{e:04x},', end='')

print()
print(f'event signature {esmagic} found every {BL} samples: clean data set')


tb = np.linspace(2, BL, num=BL-2)

nstack = 200

print(ubursts[0:nstack,2:BL].shape)
print(tb.shape)

stack = []
stack_off = 25          # offset value to create stack
for b in range(nstack):
    stack.append(ubursts[b,2:BL] + b*stack_off)

for b in range(nstack):
    plt.plot(tb, stack[b])
plt.title(f'Stacked Plot of {nstack} bursts each {BL} samples, offset {stack_off} codes per plot')
plt.show()

nstack = 5
for b in range(nstack):
    plt.plot(tb, stack[b])
plt.title(f'Stacked Plot of {nstack} bursts each {BL} samples, offset {stack_off} codes per plot')
plt.show()




