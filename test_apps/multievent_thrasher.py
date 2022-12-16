#!/usr/bin/env python3
''' test program for multivent. 
1 autotriggers
2 waits for data, analyses data, repeats 1

[pgm@hoy5 acq400_hapi]$ ./test_apps/multievent_thrasher.py --help
usage: multievent_thrasher.py [-h] [-i INITIAL] [-s STEP] [-m MAX] [-t THRESHOLD] [-n MAX_TESTS] [--sig_gen SIG_GEN] [--root ROOT] uuts

Multivent Thrash Test

positional arguments:
  uuts                  uut dns name or ip

options:
  -h, --help            show this help message and exit
  -i INITIAL, --initial INITIAL
                        Initial prepost samples
  -s STEP, --step STEP  Sample increase amount
  -m MAX, --max MAX     Max samples before stop max 100,000
  -t THRESHOLD, --threshold THRESHOLD
                        number of shots before write log and stepping samples
  -n MAX_TESTS, --max_tests MAX_TESTS
                        maximum tests to do
  --sig_gen SIG_GEN     dns name or ip-address of remote FG
  --root ROOT           data root path for arriving data files

'''

import os
import time
import numpy as np
import argparse
import acq400_hapi
import subprocess

args = None
padding = {}
logger = {}

def main(args):
    current = None
    test_num = 1
    uut = setup(args)
    while True:
        log("Test {}".format(test_num), prYellow)

        current = get_event(current)
        check_event(current)

        log_event(test_num)

        reset_test(test_num, uut, args.max_tests)

        clean([current])
        test_num += 1
        print('\n')

def clean(files_to_erase):
    for filename in files_to_erase:
        filepath = "{}/{}".format(args.data_path, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            prYellow("Erasing " + filename)

def erase_all_events():
    files = sorted(os.listdir(args.data_path))
    for filename in files:
        if filename[-4:] == '.dat':
            clean([filename])

def get_stream_state(uut):
    return acq400_hapi.pv(uut.s0.CONTINUOUS_STATE)

def start_stream(uut):
    state = get_stream_state(uut)
    while not state in ['IDLE','CLEANUP']:
        time.sleep(1)
        state = get_stream_state(uut)
    prYellow("Starting Stream")
    uut.s0.CONTINUOUS = 'start'
    while state != "RUN":
        print("Waiting for start")
        state = get_stream_state(uut)
        time.sleep(1)
    prGreen("Stream Started")

def stop_stream(uut):
    state = get_stream_state(uut)
    if state in ['RUN','ARM']:
        prYellow("Stopping Stream")
        uut.s0.CONTINUOUS = 'stop'

def set_padding(uut, new):
    log("Setting Pre/Post Samples to: {}".format(new), prYellow)
    uut.s1.MEV_POST = new
    uut.s1.MEV_PRE = new
    time.sleep(2)

def setup(args):
    padding['current'] = args.initial
    padding['step'] = args.step
    padding['max'] = args.max
    padding['threshold'] = args.threshold
    logger['errors'] = 0
    logger['buffer'] = []
    logger['file'] = None
    logger['time'] = 0
    logger['worst'] = 0
    if(args.max_tests < args.threshold and args.max_tests != 0):
        exit("Error: threshold larger than max_tests")

    uut = acq400_hapi.Acq400(args.uuts[0], monitor=False)
    uut.s1.EVENT0 = 'enable'
    uut.s1.EVENT0_SENSE = 'rising'
    uut.s0.SIG_SRC_TRG_0 = "EXT"
    uut.s1.MEV_MAX = 100

    set_padding(uut, padding['current'])
    prYellow("Threshold is {} tests".format(padding['threshold']))
    clean(['latest'])
    erase_all_events()

    stop_stream(uut)
    start_stream(uut)
    return uut

####    
def get_event(current):
    timestart = time.time()
    send_trigger()
    event =  get_new_event(current)
    log_time(timestart);
    return event

def send_trigger():
    if args.sig_gen:
        log("Sending Trigger", prYellow)
        acq400_hapi.Agilent33210A(args.sig_gen).trigger()
    else:
        print("Ready for trigger")

def get_new_event(current):
    second_chance = True
    count = 0
    sleep = 0.1
    while True:
        latest = get_latest()
        if count > 20:
            if not second_chance:
                exit("Error: Timeout exceeded is wingman running?")
            error("Error: No file received trying again")
            count = 0
            second_chance = False
            time.sleep(5)
            send_trigger()

        if latest != current:
            if latest == "ERROR":
                exit("Error  received")
            if latest != "":
                log("Received: {}".format(latest), prGreen)
                return latest
        print('Waiting for new Event {}s'.format(round(count,2)), end='\r')
        count += sleep
        time.sleep(sleep)

def get_latest():
    filename = 'latest'
    filepath = "{}/{}".format(args.data_path, filename)
    if not os.path.isfile(filepath):
        return None
    line = open(filepath, 'r').readline().strip()
    return line

####
def check_event(current):
    filepath = "{}/{}".format(args.data_path, current)
    data_array = np.fromfile(filepath, dtype=np.int32)
    #data_array = np.fromfile(filepath, dtype=np.uint32)
    """
    count = 0
    max_unsigned_32 = 1 << 32
    for num in data_array:
        if num < 0:
            num = max_unsigned_32 + num
        count += 1
        print("{} {}".format(hex(num), count))
        if  count == 100:
            exit()
            pass
        pass
    exit()
    """
    #data_array.shape = (-1,52)
    data_array.shape = (-1,20)
    check_event_signatures(get_event_signatures(data_array), current)
    check_sample_order(data_array, current)
    get_filesize(current)
    del data_array

def get_event_signatures(data_array):
    events = []
    es = 0xaa55f151 #event signature
    es = 0xaa55f151
    max_unsigned_32 = 1 << 32

    array_len = len(data_array)
    for i in range(0, array_len):
        num = data_array[i][1]
        if num < 0:
            num = max_unsigned_32 + num
        if num == es:
            events.append(i)
    return events 

def check_event_signatures(events, current):
    if not events:
        error("Error: No Event Signature found got: {}".format(events))
        archive_error(current)
    for i, event in enumerate(events):
        if i > 0:
            error("Error: Extra event found at {}".format(event))
            archive_error(current)
        if event - padding['current'] == 0:
            log("Event {} is a right position {}".format(i, event), prGreen)
        else:
            error("Error: Event {} is a wrong position {}".format(i, event))
            archive_error(current)

def check_sample_order(data_array, latest):
    sc = 16
    array_len = len(data_array)
    previous = data_array[0][sc] - 1
    for i in range(0, array_len):
        current = data_array[i][sc]
        diff = current - previous
        know_errors = [-1956863,1956865]
        if diff != 1:
            if diff in know_errors:
                log("Sample count rolled back?", prCyan)
                error("Known Error: {} Sample wrong Current is: {} Previous was: {} Diff is {}".format(i, current, previous, diff))
                archive_error(latest)
                return
            error("Error: {} Sample wrong Current is: {} Previous was: {} Diff is {}".format(i, current, previous, diff))
            archive_error(latest)
            return
        previous = current
    log("{} samples in order".format(array_len), prGreen)

def get_filesize(filename):
    event_file = "{}/{}".format(args.data_path, filename)
    size = round(os.path.getsize(event_file)/(1<<20))
    log("File is {}MB".format(size), prYellow)

####
def log_event(test_num):
    global logger
    if test_num % padding['threshold'] == 0:
        logger['file'] = create_log_filename(test_num)
        write_log()

def log(message, color = None):
    global logger
    if color:
        color(message)
    logger['buffer'].append("{}\n".format(message))

def error(message):
    global logger
    log(message, prRed)
    logger['errors'] += 1

def log_time(start):
    global logger
    timetaken = round(time.time() - start,2)
    log("{}s elapsed".format(timetaken), prYellow)
    logger['time'] += timetaken
    if timetaken > logger['worst']:
        prYellow("New worst time! {}s".format(timetaken))
        logger['worst'] = timetaken
        pass

def create_log_filename(test_num):
    test_start = int((test_num - 1) / padding['threshold']) * padding['threshold'] + 1
    return "Tests[{}-{}]{}-{}.log".format(test_start, test_num, padding['current'], padding['current'])

def write_log():
    global logger
    average_time = round(logger['time'] / padding['threshold'], 2) 
    log("writing log to file ", prYellow)
    log("Total Errors: {}".format(logger['errors']))
    log("Average time: {}s".format(average_time))
    log("Worst time: {}s".format(logger['worst']))
    with open(logger['file'] ,'a') as f:
        f.writelines(logger['buffer'])
        f.close()
    logger['buffer'] = []
    logger['errors'] = 0
    logger['time'] = 0
    logger['worst'] =  0

def archive_error(name):
    prRed("Archiving error")
    dest = "{}.error".format(name)
    cmd = "cp {}/{} {}/{}".format(args.data_path, name, args.data_path, dest)
    #print(cmd)
    os.system(cmd)
    time.sleep(1)
####
def reset_test(test_num, uut, max_tests):
    #change slowmon freq here
    #slomon(freq) ?
    if test_num % padding['threshold'] == 0:
        if max_tests > 0:
            if test_num >= max_tests:
                exit("max tests reached")
            increase_samples(uut)
        else:
            if not increase_samples(uut):
                exit("Max samples reached")
    fix_stream(test_num, uut)

def increase_samples(uut):
    global padding
    if padding['current'] < padding['max']:
        padding['current'] += padding['step']
        set_padding(uut, padding['current'])
        return True
    return False

def fix_stream(test_num, uut):
    if test_num % 100 == 0:
        log("Fixing stream", prYellow)
        uut.s1.MEV_MAX = 100
        stop_stream(uut)
        start_stream(uut)
    #if test_num % 1000 == 0:
    #strange behaviour :(
        #stop_stream(uut)
        #start_stream(uut)


def prRed(skk): print("\033[91m{}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m{}\033[00m" .format(skk)) 
def prYellow(skk): print("\033[93m{}\033[00m" .format(skk)) 
def prPurple(skk): print("\033[95m{}\033[00m" .format(skk)) 
def prCyan(skk): print("\033[96m{}\033[00m" .format(skk)) 
def prBlue(skk): print("\033[94m{}\033[00m" .format(skk))

def cmdArgs():
    global args
    parser = argparse.ArgumentParser(description='Multivent Thrash Test')
    parser.add_argument('-i', '--initial', default=5000, type=int, help='Initial prepost samples')
    parser.add_argument('-s', '--step', default=5000, type=int, help='Sample increase amount')
    parser.add_argument('-m', '--max', default=100000, type=int, help='Max samples before stop max 100,000')
    parser.add_argument('-t', '--threshold', default=100, type=int, help='number of shots before write log and stepping samples')
    parser.add_argument('-n', '--max_tests', default=0, type=int, help='maximum tests to do')
    parser.add_argument('--sig_gen', default=None, type=str, help='dns name or ip-address of remote FG')    
    parser.add_argument('--root', default='/home/dt100/DATA/{}', help='data root path for arriving data files')
    parser.add_argument('uuts', nargs = 1, help="uut  dns name or ip")
    
    args = parser.parse_args()
    args.data_path = args.root.format(args.uuts[0])
    return args

if __name__ == '__main__':
    main(cmdArgs())
