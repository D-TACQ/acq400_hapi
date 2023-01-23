#!/usr/bin/env python3

import urllib.request
import time
import sys

def wait_ready(uut):
    while True:
        try:
            contents = urllib.request.urlopen("http://{}/d-tacq/rc-local-complete".format(uut)).read()
            print(contents)
            return True
        except:
            print("{} not ready".format(uut))
            time.sleep(2)

if __name__ == '__main__':
    wait_ready(sys.argv[1])



