# acq400_hapi: acq400 Host API

python module to connect to remote hosts. [Documentation](https://d-tacq.github.io/acq400_hapi_docs/index.html)

## Installation

### Use Latest Github
**Recommended**
... and use PYTHONPATH to reference the library when used from anywhere
```bash
mkdir PROJECTS; cd PROJECTS
git clone https://github.com/D-TACQ/acq400_hapi
cd acq400_hapi

#export PYTHONPATH=~/PROJECTS/acq400_hapi

on Linux,   run: source ./setpath
on Windows, run: SETPYTHONPATH.BAT      # then start a new shell.
```

### Standard method use PIP
**[Currently Deprecated : please use Github above]**

PIP has the advantage of installing a system library, however it's not updated as frequently as the Github source, so some feature may be lacking.

V2.0.0 : works with Python 2.7 and 3.x

Python 2.x needs the "future" feature:
on linux:
    sudo pip install future
on Windows:
    py -version -m pip install future

RECOMMENDATION: install with PIP:
pip install acq400_hapi

**Python 2.x is now deprecated, please try to use Python3. On systems where python 2 is the default, there is usually a python3 runtime, recommended**



That way, "import acq400_hapi" is available from wherever the program is run.

To run the apps, user_apps or test_apps, clone this repo.
The connectivity package is available globally as a library from pip, or you can
run the code in acq400_hapi directly, by using PYTHONPATH

## API Documentation

### Library
http://www.d-tacq.com/resources/HAPI/acq400_hapi/index.html
### Example Applications
http://www.d-tacq.com/resources/HAPI/user_apps/index.html



## How it works

class Acq400 nails up a socket connection to all the site servers at 4220+s,
as well as running a status monitor thread on 2235 and
allowing access to post-shot data on 53000+ch

each knob on the site is presented as a property of the connection, so that
simple bash-script-like syntax can be used

**NOTE** on Name Service:
HAPI uses regular DNS for name resolution.
*Ideally* your UUT has a DNS name that matches the hostname

How to tell?
ping acq2106_123

If that works, you have DNS.
If it doesn't, well HAPI will work with a raw IP address, but it's much clearer to set up a "local DNS".
All our examples use the convention hostname IS dnsname.

The "local DNS" doesn't have to be full DNS subsystem, all you need is to set the name mapping in your system's hosts file:
 * Linux : /etc/hosts/
 * Windows : C:\Windows\System32\Drivers\etc\hosts



```python
uut.s0.set_arm=1

Example: running a session interactively while a test loop is running:
>>> import acq400_hapi
>>> uut = acq400_hapi.factory("10.12.132.22")
>>> uut.s1.shot
'348'
>>> uut.s1.shot
'348'
>>> uut.s1.shot
'349'
```

The goal is to make it easy to remote-script multiple uut's.

Example:
```python
import acq400_hapi
uut1 = acq400_hapi.factory("acq1001_144")
uut2 = acq400_hapi.factory("acq1001_145")

for ii in range(0,10):
	c1 = uut1.s1.SIG_SAMPLE_COUNT_COUNT.split(" ")[1]
	c2 = uut2.s1.SIG_SAMPLE_COUNT_COUNT.split(" ")[1]
	print("%s %s" % (c1, c2))
11078689363247 11078689363247
11078689363247 11078689363247
11078739404360 11078739404360
11078739404360 11078739404360
11078739404360 11078789398809
11078789398809 11078789398809
11078789398809 11078789398809
11078839399330 11078839399330
11078839399330 11078839399330
```

... and yes, these are EPICS PV's, so we could use capy.
But, this way, it's all vanilla python, no other installs required.

Note also, knob names eg
```text
SIG:SAMPLE_COUNT:COUNT are auto converted to valid python identifiers:
SIG_SAMPLE_COUNT_COUNT
```
You can enumerate all the knobs with
```python
uut.s0.help()
..
uut.s6.help()

Help also takes a regex.
uut.s0.help(*COUNT)

Example:
>>> import acq400_hapi
>>> uut = acq400_hapi.factory("10.12.132.22")
>>> for f in uut.s0.help('.*FREQ'):
...     uut.s0.get_knob(f)
...
'SIG:CLK_EXT:FREQ 25007219'
'SIG:CLK_MB:FREQ 50012464'
'SIG:CLK_S1:FREQ 50010624'
'SIG:CLK_S2:FREQ 0'
'SIG:EVT_EXT:FREQ 0'
'SIG:EVT_MB:FREQ 0'
'SIG:EVT_S1:FREQ 0'
```

The Acq400 class can be fairly slow to instantiate
(imagine an ACQ2106 with 6 sites populated), but once the connections are
nailed up, then control links are fast.
=> The use case is: make the connection at the beginning, then operate over
long periods.


