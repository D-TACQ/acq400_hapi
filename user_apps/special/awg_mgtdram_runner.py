import sys
import subprocess
import tempfile
import time
import acq400_hapi


uuts = []
procs = []

uut_names = ("acq2106_293", "acq2106_294")




def run_shot(uut_names, shot, trigger):
    for uut in uut_names:
        f = open("{}/{:04d}.log".format(uut, shot), 'w')
        p = subprocess.Popen([ sys.executable, './user_apps/acq2106/mgtdramshot.py',
                          '--captureblocks', '800', '--offloadblocks', '800', uut ], stdout=f)
        procs.append((uut, p, f))
        print("spawned {}".format(uut))

    trigger()

    for uut, p, f in procs:
        p.wait()
        print("reaped {}".format(uut))
        f.close()

def trigger():
    time.sleep(2)
    print("trigger")


for name in uut_names:
    uuts.append(acq400_hapi.factory(name))
   

for u in uuts:
    u.s1.shot = 0
 
for shot in range(1,100):
    run_shot(uut_names, shot, trigger)


