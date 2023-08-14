#!/usr/bin/env python3
'''
Created on 14 Aug 2023

@author: pgm
'''

import numpy as np
import matplotlib.pyplot as plt

'''
1. ramp north from A0 to A1 in Tramp
2. decelerate north to 0 from ww
3. accelerate  south from 0 to ww
4. ramp south from A1 to A0 in Tramp
5. decelerate south from ww to 0
6. accelerate north from 0 to ww
'''
def cycloid_scan(nramp, A0, A1, nrs, alpha):
    nfull = nramp + nrs + nramp + nrs
    print(f'nfull {nfull}')
    data = np.zeros(nfull)
    AA = A1-A0
    ww = AA/nramp
    acc = (ww*ww)/(2*alpha)
    
    print(f'AA:{AA} ww:{ww} acc:{acc}')
    
    ii = 0
    # 1. ramp north from A0 to A1 in Tramp
    for ii2 in range(0, nramp):
        data[ii] = A0 + ii2 * ww
        ii += 1
    # 2. decelerate north to 0 from ww
    uu = ww
    s0 = data[ii-1]
    for ii2 in range(0, nrs//2):        
        data[ii] = s0 + uu - acc*(1*1)/2
        print(f's0:{s0} uu:{uu} data[ii]:{data[ii]}')
        if uu > 0:
            uu -= acc
        else:
            uu = 0
        s0 = data[ii]
        ii += 1
        
        
    # 3. accelerate  south from 0 to ww   
    for ii2 in range(0, nrs//2):
        data[ii] = data[ii-2*ii2-1]
        ii += 1
    # 4. ramp south from A1 to A0 in Tramp
    ww = -AA/nramp    
    for ii2 in range(0, nramp):
        data[ii] = A1 + ii2 * ww
        ii += 1
    # 5. decelerate south from ww to 0
    acc = -(ww*ww)/(2*alpha)
    uu = ww
    s0 = data[ii-1]
    for ii2 in range(0, nrs//2):
        data[ii] = s0 + uu - acc*(1*1)/2
        if uu < 0:
            uu -= acc
        else:
            uu = 0
        s0 = data[ii]
        ii += 1
    # 6. accelerate north from 0 to ww  
    for ii2 in range(0, nrs//2):
        data[ii] = data[ii-2*ii2-1]
        ii += 1
        
    return data    
    
if __name__ == '__main__':
    plt.plot(cycloid_scan(512, 1000, 11000, 256, 1200))
    plt.show()
    pass