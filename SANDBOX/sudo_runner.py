#!/usr/bin/env python3

import os
import sys


try:
    uut = sys.argv[1]
except:
    uut = "acq2106_999"

os.system(f"sudo UUT={uut} ./run_me_as_root")


