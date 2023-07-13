#!/usr/bin/env python3

import urllib.request

class Calibfit:
    def __init__(self, uutname):
#1234567
        url = f"http://{uutname}/tmp/calibfit.log"
        print(url)
        contents = urllib.request.urlopen(url).read().decode('utf-8')

        self.calib = {}

        for line in contents.split('\n'):
            if len(line) > 1:
                ch, sns, tau, I0, Q0 = line.split()
            self.calib[int(ch)] = [float(x) for x in (sns, tau, I0, Q0)]

    def sns(self, ch):
        return self.calib[ch][0]

    def tau(self, ch):
        return self.calib[ch][1]

    def I0(self, ch):
        return self.calib[ch][2]

    def Q0(self, ch):
        return self.calib[ch][3]

def run_unit_test():
    cb = Calibfit('acq2106_123')
    for ch in sorted(cb.calib.keys()):
        print(f'ch:{ch} sns:{cb.sns(ch)} tau:{cb.tau(ch)}')

if __name__ == '__main__':
    run_unit_test()




