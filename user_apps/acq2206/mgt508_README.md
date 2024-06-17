# README for MGT508

 ## Typical transcript

```
peter@danna:~/PROJECTS/acq400_hapi$ ./user_apps/acq2206/mgt508_capture.py --simulate=0 --GB=4 --clear_mem=0 acq2206_055,mgt508-003
uut_pairs: ['acq2206_055,mgt508-003']
Start pull mgt508-003

.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|.......
Pull Complete
Capture 127 time 2.2 sec 1843 MB/s
TIMING:func:'wait_pull_complete' took: 42.60 sec
mgt508_read_mem MGT=mgt508-003 GB=4
removing old data from mgt508-003
mgt508-003 clean
fixing file size to be an integer # samples: 134217696 (1398101.0)
mgt508-003/000001/0000 len 127 MB total 0.1 GB
mgt508-003/000001/0001 len 127 MB total 0.2 GB
mgt508-003/000001/0002 len 127 MB total 0.4 GB
mgt508-003/000001/0003 len 127 MB total 0.5 GB
mgt508-003/000001/0004 len 127 MB total 0.6 GB
mgt508-003/000001/0005 len 127 MB total 0.7 GB
mgt508-003/000001/0006 len 127 MB total 0.9 GB
mgt508-003/000001/0007 len 127 MB total 1.0 GB
mgt508-003/000001/0008 len 127 MB total 1.1 GB
mgt508-003/000001/0009 len 127 MB total 1.2 GB
mgt508-003/000001/0010 len 127 MB total 1.4 GB
mgt508-003/000001/0011 len 127 MB total 1.5 GB
mgt508-003/000001/0012 len 127 MB total 1.6 GB
mgt508-003/000001/0013 len 127 MB total 1.7 GB
mgt508-003/000001/0014 len 127 MB total 1.9 GB
mgt508-003/000001/0015 len 127 MB total 2.0 GB
mgt508-003/000001/0016 len 127 MB total 2.1 GB
mgt508-003/000001/0017 len 127 MB total 2.2 GB
mgt508-003/000001/0018 len 127 MB total 2.4 GB
mgt508-003/000001/0019 len 127 MB total 2.5 GB
mgt508-003/000001/0020 len 127 MB total 2.6 GB
mgt508-003/000001/0021 len 127 MB total 2.7 GB
mgt508-003/000001/0022 len 127 MB total 2.9 GB
mgt508-003/000001/0023 len 127 MB total 3.0 GB
mgt508-003/000001/0024 len 127 MB total 3.1 GB
mgt508-003/000001/0025 len 127 MB total 3.2 GB
mgt508-003/000001/0026 len 127 MB total 3.4 GB
mgt508-003/000001/0027 len 127 MB total 3.5 GB
mgt508-003/000001/0028 len 127 MB total 3.6 GB
mgt508-003/000001/0029 len 127 MB total 3.7 GB
mgt508-003/000001/0030 len 127 MB total 3.9 GB
mgt508-003/000001/0031 len 127 MB total 4.0 GB

File mgt508-003/000001/0032 length 0 mtime Mon Jun 17 10:29:23 2024
Return code : 0
TIMING:func:'read_data' took: 37.10 sec

```
 ### Annotated Transcript
  #### --help
```
peter@danna:~/PROJECTS/acq400_hapi$ ./user_apps/acq2206/mgt508_capture.py --help
usage: mgt508_capture.py [-h] [--simulate SIMULATE] [--clear_mem CLEAR_MEM] [--GB GB] uut_pairs [uut_pairs ...]

Controls acq2206+mgt508 deep memory system

positional arguments:
  uut_pairs             acq2206,mgt508 [a,m] ..

options:
  -h, --help            show this help message and exit
  --simulate SIMULATE   use simulated data and validate
  --clear_mem CLEAR_MEM
                        zero memory before run
  --GB GB               capture length in gigabytes
 ```
  #### transcript
```
Capture 4GB data from  acq2206_055 and mgt508-003
First there's a long delay while the system readies itself (from power up, with 6xACQ480), 40s).
Then we see a data pattern, these are capture DMA buffers, each 32MB long. eg 
.........| == 320MB
The actual capture, 4GB takes 2.2s
```
```
peter@danna:~/PROJECTS/acq400_hapi$ ./user_apps/acq2206/mgt508_capture.py --simulate=0 --GB=4 --clear_mem=0 acq2206_055,mgt508-003
uut_pairs: ['acq2206_055,mgt508-003']
Start pull mgt508-003

.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|.......
Pull Complete
Capture 127 time 2.2 sec 1843 MB/s
TIMING:func:'wait_pull_complete' took: 42.60 sec
```
```
Next we offload the data to a series of files. This is the same process as live Ethernet streaming, except of course now the data is stored in DRAM in MGT508.
Example shows 4GB stored to disck in 37s por 108MB/s:
```
```
mgt508_read_mem MGT=mgt508-003 GB=4
removing old data from mgt508-003
mgt508-003 clean
fixing file size to be an integer # samples: 134217696 (1398101.0)
mgt508-003/000001/0000 len 127 MB total 0.1 GB
mgt508-003/000001/0001 len 127 MB total 0.2 GB
mgt508-003/000001/0002 len 127 MB total 0.4 GB
..
mgt508-003/000001/0029 len 127 MB total 3.7 GB
mgt508-003/000001/0030 len 127 MB total 3.9 GB
mgt508-003/000001/0031 len 127 MB total 4.0 GB

File mgt508-003/000001/0032 length 0 mtime Mon Jun 17 10:29:23 2024
Return code : 0
TIMING:func:'read_data' took: 37.10 sec
```
 ## Data Plot Example
```
~/PROJECTS/acq400_hapi$ ./user_apps/analysis/host_demux.py --src mgt508-003/000001/0000 --pchan 1,3,9,10,11,13,15  --egu=1 --pses=0:2000:1 acq2206_055 &
```
![plot result](https://github.com/D-TACQ/acq400_hapi/releases/download/v2.14.1/Screenshot.from.2024-06-17.08-52-23.png)


 ## 14GB simulation run with validation;

```
Shows a 14GB run with offload and validation at full line rate 112MB/s
```
```
peter@danna:~/PROJECTS/acq400_hapi$ ./user_apps/acq2206/mgt508_capture.py --simulate=1 --GB=14 --clear_mem=0 acq2206_055,mgt508-003
uut_pairs: ['acq2206_055,mgt508-003']
Start pull mgt508-003

.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|......
Pull Complete
Capture 446 time 7.8 sec 1833 MB/s
TIMING:func:'wait_pull_complete' took: 27.60 sec
mgt508_read_mem mgt508-003 14 24
14.0GiB 0:02:07 [ 112MiB/s] [                                                              <=>                                                  ]
2024-06-17.09:45:40 bytes: 0x0000095500de    156565726 13.998 GB   0.00 MB/s errors: 0 CLEAN

real	2m7.893s
user	0m2.392s
sys	0m11.057s
Return code : 0
TIMING:func:'read_data' took: 127.94 sec

```
 ## Deferred work scripts
 * mgt508_capture.py defers work to 3 scripts:
  1. scripts/mgt508_clear_mem   # optionally, clear the DRAM on MGT508 (not needed in normal operation)
  2. scripts/mgt508_read_mem    # uses acq400_stream2.py to read data to a series of consecutive files
  3. scripts/mgt508_validate_mem # uses isramp, a C++ program from AFHBA404/FUNCTIONAL_TESTS to validate the data.
  
  ## End
  
  
 

