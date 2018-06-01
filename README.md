# acq400_hapi: acq400 Host API

python module to connect to remote hosts

* acq400_hapi: source code for the connectivity package
* user_apps : example user client applications
* test_apps : more detailed validations

## Installation

V2.0.0 : works with Python 2.7 and 3.x

Now needs the "future" feature:
on linux:
    sudo pip install future
on Windows:
    py -version -m pip install future

RECOMMENDATION: install with PIP:
pip install acq400_hapi

That way, "import acq400_hapi" is available from wherever the program is run.

To run the apps, user_apps or test_apps, clone this repo.
The connectivity package is available globally as a library from pip, or you can
run the code in acq400_hapi directly, by using PYTHONPATH

## API Documentation
https://D-TACQ.github.io/acq400_hapi/html/acq400_hapi/index.html


## How it works

class Acq400 nails up a socket connection to all the site servers at 4220+s,
as well as running a status monitor thread on 2235 and 
allowing access to post-shot data on 53000+ch

each knob on the site is presented as a property of the connection, so that 
simple bash-script-like syntax can be used

```python
uut.s0.set_arm=1

Example: running a session interactively while a test loop is running:
>>> import acq400_hapi
>>> uut = acq400_hapi.Acq400("10.12.132.22", monitor=False)
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
from acq400_hapi import *
uut1=acq400.Acq400("acq1001_144")
uut2=acq400.Acq400("acq1001_145")

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
>>> uut = acq400_hapi.Acq400("10.12.132.22", monitor=False)
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

## TODO:
* add a 4210 socket for live stream?. 
* instantiate the uut, site clients in parallel


