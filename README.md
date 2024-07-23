# acq400_hapi: acq400 Host API

* A Python module ./acq400_hapi to connect to remote hosts, 
* a large set of example client programs ./user_apps

* [Documentation](https://d-tacq.github.io/acq400_hapi_docs)

## Installation

#### Requirements
	python3
		numpy
		matplotlib

### recommended: Using Pip
  
Clone/update latest version from GitHub, then install in-place using `pip` using a dedicated script

```bash

$  git  clone  https://github.com/D-TACQ/acq400_hapi
$  cd  acq400_hapi
$  pip3 install -e .

```

This creates a system-wide link to the local folder so that Python knows where to find `acq400_hapi` on your system. 

Then whenever desired, run `git pull` in the source folder to update from git,

no further installation step required.

It's also possible to install a PIP from PYPI, however the package on PYPI will likely be out of date, so this is not recommended.

### alternate: Using PythonPath
```bash

$  git  clone  https://github.com/D-TACQ/acq400_hapi
$  cd  acq400_hapi

on Linux,   run: source ./setpath
on Windows, run: SETPYTHONPATH.BAT # restart shell.

```

## Usage

```python
import acq400_hapi
```

## How it works

The `Acq400` class nails up a socket connection to all the site servers at 4220+s, as well as
running a status monitor thread on 2235 and allowing access to post-shot data on 53000+ch.

Each knob on the site is presented as a property of the connection, so that simple
bash-script-like syntax can be used.

**NOTE** on Name Service: HAPI uses regular DNS for name resolution. *Ideally* your UUT has a
DNS name that matches the hostname. Check by pinging:

```bash
ping acq2106_123
```

If that works, you have DNS. If it doesn't, well HAPI will work with a raw IP address, but
it's much clearer to set up a "local DNS". All our examples use the convention hostname IS
dnsname.

The "local DNS" doesn't have to be full DNS subsystem, all you need is to set the name mapping
in your system's hosts file:

 * Linux : /etc/hosts/
 * Windows : C:\Windows\System32\Drivers\etc\hosts


### Running a session interactively while a test loop is running:

```python
>>> import acq400_hapi
>>> uut = acq400_hapi.factory("10.12.132.22")
>>> uut.s1.shot
'348'
>>> uut.s1.shot
'348'
>>> uut.s1.shot
'349'
```

The goal is to make it easy to remote-script multiple uut's:

```python
>>> import acq400_hapi
>>> uut1 = acq400_hapi.factory("acq1001_144")
>>> uut2 = acq400_hapi.factory("acq1001_145")

>>> for ii in range(0,10):
...    c1 = uut1.s1.SIG_SAMPLE_COUNT_COUNT.split(" ")[1]
...    c2 = uut2.s1.SIG_SAMPLE_COUNT_COUNT.split(" ")[1]
...    print("%s %s" % (c1, c2))
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

...and yes, these are EPICS PV's, so we could use capy. But, this way, it's all vanilla
Python, no other installs required.

### Knob names

```text
SIG:SAMPLE_COUNT:COUNT are auto converted to valid python identifiers:
SIG_SAMPLE_COUNT_COUNT
```

You can enumerate all the knobs with:

```python
>>> uut.s0.help()
..
>>> uut.s6.help()
```

Help also takes a regex:

```python
>>> uut.s0.help(*COUNT)
```

Example:

```python
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

### Speed

The `Acq400` class can be fairly slow to instantiate (imagine an ACQ2106 with 6 sites
populated), but once the connections are nailed up, then control links are fast. The use case
is to set up the connection once, then operate over long periods.
