import argparse
import os
import time

import acq400_hapi

SAMPLESZ = 16

def run_shot(uut, shot, fn):
    print("run_shot {} {}".format(shot, fn))
    uut.s1.playloop_maxlen = os.stat(fn).st_size/SAMPLESZ
    t1 = time.time()
    os.system('cat {} | pv | nc {} 54203 1>/dev/null'.format(fn, uut.uut))
    t2 = time.time()
    while uut.s1.AWG_SHOT_COMPLETE.split(' ')[1] != '1':
        time.sleep(0.1)
    t3 = time.time()
    return( t1, t2, t3)
    

def run_test(args):
    uut = acq400_hapi.Acq400(args.uut)
    uut.s1.shot = '0'
    times = []
    for shot in range(0, args.reps):
        for fn in args.files:
            times.append(run_shot(uut, shot, fn))
    
    totalplay = 0
    for shot in times:
        playtime = shot[2] - shot[0]
        totalplay += playtime
        print("{}".format(shot[2] - shot[0]))
   
    print("mean {}".format(totalplay/len(times)))
       

def run_main():
    parser = argparse.ArgumentParser(description = 'awg speed test')
    parser.add_argument('--reps', type=int, default=1, help='number of repetitions')
    parser.add_argument('--uut',  default=None, help='uut')
    parser.add_argument('files', nargs='+', help='files to play')
    run_test(parser.parse_args())

if __name__ == '__main__':
    run_main()

