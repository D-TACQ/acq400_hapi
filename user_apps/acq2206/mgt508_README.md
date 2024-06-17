# README for MGT508

# Typical transcript

```
peter@danna:~/PROJECTS/acq400_hapi$ ./user_apps/acq2206/mgt508_capture.py --simulate=0 --GB=4 --clear_mem=0 acq2206_055,mgt508-003
uut_pairs: ['acq2206_055,mgt508-003']
Start pull mgt508-003
.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|.........|.........|.........|.........|
.........|.........|.........|.........|......
Pull Complete
Capture 446 time 7.8 sec 1835 MB/s
TIMING:func:'wait_pull_complete' took: 49.48 sec
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

File mgt508-003/000001/0032 length 0 mtime Mon Jun 17 09:11:13 2024
Return code : 0
TIMING:func:'read_data' took: 66.33 sec
```
