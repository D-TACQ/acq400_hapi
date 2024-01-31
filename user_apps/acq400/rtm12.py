#!/usr/bin/env python

''' run an rtm12 shot, providing 3 triggers

    The rtm12 feature allows a shot to be run as 2 bursts of different length
    This setup requires 3 triggers:
        trigger start of capture
        trigger first burst
        trigger second burst
    Then, because a TRANSIENT capture will almost always required a data flush,
        further burst triggers until the capture stops

    We show an example with either soft triggers or WR triggers (txi)

    Sequence
    S0. Disable TRG out.
    S1. SetArm
    S1.5 WaitArm
    S2. Send Start trigger
    S3. Enable TRG out
    S4. Send BURST1_TRG
    S5. Wait State RUN
    S6. If BLEN1 > 1 DMA BUFFER:   poll sample count until we have enough count.
If we only start looking at SAMPLE_COUNT after transition to ARM, then we don't have to worry about the non-zero start.

    S7. Send BURST2_TRG
    S8. Wait State IDLE (complete.

example::

    # Trivial example soft,soft,soft
    /rtm12.py --trg=soft,soft,soft --rtm12=25000,125000 acq1001_084

    #WR example: soft,txi,txi
    /rtm12.py --trg=soft,txi,txi --rtm12=25000,125000 acq1001_084

    soft operates on TRG.d1, txi triggers WRTT1, so it operates on TRG.d1 also

    # transcript: shows the 3 triggers being fired at earliest opportunity.

    ./user_apps/acq400/rtm12.py --trg=soft,txi,txi --rtm12=20000,500000 --plot=1 acq2106_274

    
Transcript::

    sam@humla:~/PROJECTS/acq400_hapi$ ./user_apps/acq400/rtm12.py --trg=soft,soft,soft --rtm12=25000,125000 --plot=1 acq2106_007
    Burst1 below minimum increasing to 1 buffer
    0 soft
    1 soft
    2 soft
    uut ['acq2106_007']
    rtm12 [131072, 724288]
    trg ['soft', 'soft', 'soft']
    [trigger capture]
    Sending trigger soft
    [trigger burst1]
    Sending trigger soft
    waiting for burst1
    waiting for burst1
    [trigger burst2]
    Sending trigger soft
    trigger again to force flush
    Sending trigger soft
    [wait stopped]
    Triggers script 4 uut SIG:TRG_MB:COUNT 4
    plotting

    sam@humla:~/PROJECTS/acq400_hapi$ SITECLIENT_TRACE=1 ./user_apps/acq400/rtm12.py --trg=soft,soft,soft --rtm12=25000,125000 --plot=1 acq2106_007
    Siteclient(acq2106_007, 4220) >MODEL
    Siteclient(acq2106_007, 4220) <acq2106
    Siteclient(acq2106_007, 4220) >is_tiga
    Siteclient(acq2106_007, 4220) <none
    Siteclient(acq2106_007, 4220) >is_tiga
    Siteclient(acq2106_007, 4220) <none
    Siteclient(acq2106_007, 4220) >has_mgt
    Siteclient(acq2106_007, 4220) <12 13
    Siteclient(acq2106_007, 4220) >has_mgtdram
    Siteclient(acq2106_007, 4220) <14
    Siteclient(acq2106_007, 4220) >has_mgt
    Siteclient(acq2106_007, 4220) <12 13
    Siteclient(acq2106_007, 4220) >has_mgtdram
    Siteclient(acq2106_007, 4220) <14
    Siteclient(acq2106_007, 4220) >SITELIST
    Siteclient(acq2106_007, 4220) <216,1=480,2=480
    Siteclient(acq2106_007, 4221) >module_name
    Siteclient(acq2106_007, 4222) >module_name
    Siteclient(acq2106_007, 4222) <acq480fmc
    Siteclient(acq2106_007, 4221) <acq480fmc
    Siteclient(acq2106_007, 4220) >state
    Siteclient(acq2106_007, 4220) <0 0 855360 1441792 0 647 0
    Siteclient(acq2106_007, 4220) >has_mgt
    Siteclient(acq2106_007, 4220) <12 13
    Siteclient(acq2106_007, 4220) >bufferlen
    Siteclient(acq2106_007, 4220) <4194304
    Siteclient(acq2106_007, 4220) >ssb
    Siteclient(acq2106_007, 4220) <32
    Burst1 below minimum increasing to 1 buffer
    Siteclient(acq2106_007, 4220) >SIG:TRG_MB:RESET=1
    Siteclient(acq2106_007, 4220) <
    0 soft
    Siteclient(acq2106_007, 4221) >trg=1,1,1
    Siteclient(acq2106_007, 4221) <
    1 soft
    Siteclient(acq2106_007, 4221) >rgm=3,1,1
    Siteclient(acq2106_007, 4221) <
    2 soft
    uut ['acq2106_007']
    rtm12 [131072, 724288]
    trg ['soft', 'soft', 'soft']
    Siteclient(acq2106_007, 4220) >SIG:SYNC_OUT:TRG=0
    Siteclient(acq2106_007, 4220) <
    Siteclient(acq2106_007, 4220) >transient=PRE=0 POST=855360 SOFT_TRIGGER=0
    Siteclient(acq2106_007, 4220) <
    Siteclient(acq2106_007, 4220) >rtm12=131072 724288
    Siteclient(acq2106_007, 4220) <
    Siteclient(acq2106_007, 4221) >sample_count
    Siteclient(acq2106_007, 4221) <1579654
    Siteclient(acq2106_007, 4220) >set_arm=1
    Siteclient(acq2106_007, 4220) <
    [trigger capture]
    Sending trigger soft
    Siteclient(acq2106_007, 4220) >SIG:SRC:TRG:1
    Siteclient(acq2106_007, 4220) <SIG:SRC:TRG:1 STRIG
    Siteclient(acq2106_007, 4220) >soft_trigger=1
    Siteclient(acq2106_007, 4220) <
    [trigger burst1]
    Siteclient(acq2106_007, 4220) >SIG:SYNC_OUT:TRG=2
    Siteclient(acq2106_007, 4220) <
    Siteclient(acq2106_007, 4220) >SIG:SYNC_OUT:TRG:DX=1
    Siteclient(acq2106_007, 4220) <
    Sending trigger soft
    Siteclient(acq2106_007, 4220) >SIG:SRC:TRG:1
    Siteclient(acq2106_007, 4220) <SIG:SRC:TRG:1 STRIG
    Siteclient(acq2106_007, 4220) >soft_trigger=1
    Siteclient(acq2106_007, 4220) <
    Siteclient(acq2106_007, 4221) >sample_count
    Siteclient(acq2106_007, 4221) <0
    Siteclient(acq2106_007, 4221) >sample_count
    Siteclient(acq2106_007, 4221) <0
    waiting for burst1
    Siteclient(acq2106_007, 4221) >sample_count
    Siteclient(acq2106_007, 4221) <131074
    [trigger burst2]
    Siteclient(acq2106_007, 4221) >sample_count
    Siteclient(acq2106_007, 4221) <131074
    Sending trigger soft
    Siteclient(acq2106_007, 4220) >SIG:SRC:TRG:1
    Siteclient(acq2106_007, 4220) <SIG:SRC:TRG:1 STRIG
    Siteclient(acq2106_007, 4220) >soft_trigger=1
    Siteclient(acq2106_007, 4220) <
    Siteclient(acq2106_007, 4220) >SIG:SYNC_OUT:TRG=0
    Siteclient(acq2106_007, 4220) <
    Siteclient(acq2106_007, 4221) >sample_count
    Siteclient(acq2106_007, 4221) <855364
    trigger again to force flush
    Sending trigger soft
    Siteclient(acq2106_007, 4220) >SIG:SRC:TRG:1
    Siteclient(acq2106_007, 4220) <SIG:SRC:TRG:1 STRIG
    Siteclient(acq2106_007, 4220) >soft_trigger=1
    Siteclient(acq2106_007, 4220) <
    Siteclient(acq2106_007, 4221) >sample_count
    Siteclient(acq2106_007, 4221) <855364
    [wait stopped]
    Siteclient(acq2106_007, 4220) >SIG:TRG_MB:COUNT
    Siteclient(acq2106_007, 4220) <SIG:TRG_MB:COUNT 4
    Triggers script 4 uut SIG:TRG_MB:COUNT 4
    plotting
    Siteclient(acq2106_007, 4220) >data32
    Siteclient(acq2106_007, 4220) <0
    Siteclient(acq2106_007, 4220) >transient
    Siteclient(acq2106_007, 4220) <PRE=0 POST=855360 OSAM=1 DEMUX=1 SOFT_TRIGGER=0
    Siteclient(acq2106_007, 4220) >transient
    Siteclient(acq2106_007, 4220) <PRE=0 POST=855360 OSAM=1 DEMUX=1 SOFT_TRIGGER=0
    Siteclient(acq2106_007, 4221) >ch_data_size
    Siteclient(acq2106_007, 4221) <1710720

'''

import acq400_hapi
import argparse
import time
from matplotlib import pyplot as plt


class BurstHelper():    
    def __init__(self, uut, bursts):
        self.uut = uut
        self.bursts = bursts
        bufferlen_in_samples = int(uut.s0.bufferlen) // int(uut.s0.ssb)

        if bursts[0] < bufferlen_in_samples:
            print(f"Burst1 below minimum increasing to 1 buffer")
            bursts[0] = bufferlen_in_samples
        bursts[1] += 4 * bufferlen_in_samples

        self.total_samples = sum(bursts)
        self.burst1 = bursts[0]
        self.burst2 = bursts[1]

class TriggerHelper():
    def __init__(self, uut, triggers, args):
        self.uut = uut
        self.triggers = iter(triggers)
        self.args = args
        self.total = 0
        self.total_wr = 0

        uut.s0.SIG_TRG_MB_RESET = 1
        try: uut.cC.WR_WRTT1_RESET = 1
        except: pass

        for ii, value in enumerate(triggers):
            print(f'{ii} {value}')
            if ii == 0: uut.s1.trg = f'1,1,1'
            if ii == 1: uut.s1.rgm = f'3,1,1'
    
    def select_sig_src_trg_1(self, source):
        first_time = True
        while acq400_hapi.pv(self.uut.s0.SIG_SRC_TRG_1) != source:
            if first_time:
                self.uut.s0.SIG_SRC_TRG_1 = source
                first_time = False
            time.sleep(0.1)

    def trigger(self, trg_def, delay=2):
        if self.args.trg_wait:
            input('ENTER to trigger')
        else:
            time.sleep(delay)
        print(f'Sending trigger {trg_def}')
        self.total += 1
        if trg_def == 'soft':
            self.select_sig_src_trg_1('STRIG')
            self.uut.s0.soft_trigger = '1'
        elif trg_def == 'txi':
            self.total_wr += 1
            self.select_sig_src_trg_1('WRTT1')
            # --tx_mask=2 selects WRTT1
            self.uut.s0.wrtd_txi = '--tx_mask=2 1'
        else:
            # eg set wrtd_txa
            print(f'TODO: hard_trigger {trg_def}')

    def next_trg(self):
        return next(self.triggers)

    def enable_trig_out(self):
        if self.args.trg_sync_out:
            self.uut.s0.SIG_SYNC_OUT_TRG = 'TRG'
            self.uut.s0.SIG_SYNC_OUT_TRG_DX = 'd1'

    def disable_trig_out(self):
        if self.args.trg_sync_out:
            self.uut.s0.SIG_SYNC_OUT_TRG = 'd0'

    def print_totals(self):
        print(f"Triggers script: {self.total} uut: {acq400_hapi.pv(self.uut.s0.SIG_TRG_MB_COUNT)}")
        if self.total_wr > 0:
            print(f"WR triggers script: {self.total_wr} uut: {acq400_hapi.pv(self.uut.cC.WR_WRTT1_COUNT)}")



def state_eq(uut, state):
    if uut.statmon.get_state() == state:
        return True
    return False

def state_not(uut, state):
    if uut.statmon.get_state() != state:
        return True
    return False

def run_main(args):
    assert len(args.trg) == 3, "--trg must have 3 args"
    assert len(args.rtm12) == 2, "--rtm12 must have 2 args"

    uut = acq400_hapi.factory(args.uut[0])
    bursts = BurstHelper(uut, args.rtm12)
    trg = TriggerHelper(uut, args.trg, args)

    print(f'uut {args.uut}')
    print(f'rtm12 {bursts.bursts}')
    print(f'trg {args.trg}')

    trg.disable_trig_out() # S0. Disable TRG out.

    if state_not(uut, acq400_hapi.STATE.IDLE):
        uut.s0.set_abort
        time.sleep(1)
    
    uut.s0.transient = f'PRE=0 POST={bursts.total_samples} SOFT_TRIGGER=0'
    uut.s0.rtm12 = f'{bursts.burst1} {bursts.burst2}'
    sample_count0 = int(uut.s1.sample_count)
    uut.s0.set_arm = 1 # S1. SetArm
    uut.statmon.wait_armed() # S1.5. Wait State ARM


    print("[trigger capture]")  # 
    trg.trigger(trg.next_trg()) # S2. Send Start trigger 
                                # no need to wait, system is ready for Burst Trigger
    print("[trigger burst1]")
    trg.enable_trig_out()        # S3. Enable TRG out
    trg.trigger(trg.next_trg())  # S4. Send BURST1_TRG

    while int(uut.s1.sample_count) == sample_count0:
        print("waiting for capture to start")     # S5.  Wait Run
        time.sleep(0.5)

    while int(uut.s1.sample_count) < bursts.burst1: # S6. If BLEN1 > 1 DMA BUFFER:   poll sample count until we have enough data.
        print("waiting for burst1")
        time.sleep(0.5)


    print("[trigger burst2]")
    sample_count1 = int(uut.s1.sample_count)
    trg.trigger(trg.next_trg()) # S7. Send BURST2_TRG
    trg.disable_trig_out()

    while state_eq(uut, acq400_hapi.STATE.RUNPOST):
        sample_count = int(uut.s1.sample_count)
        if sample_count > sample_count1 + bursts.burst2:
            print("trigger again to force flush")
            trg.trigger('soft', 0)
        else:
            time.sleep(0.1)


    print("[wait stopped]")
    uut.statmon.wait_stopped() # S8. Wait State IDLE (complete.
    trg.print_totals()

    if args.plot:
        print('[plotting]')
        plt.title(f"{args.uut[0]} Dual burst")
        for chan, data in enumerate(uut.read_channels(args.plot)):
            plt.plot(data, label=f"CH {args.plot[chan]}")
        plt.legend(loc='upper right')
        plt.show()
    
def list_of_values(arg):
    return [ int(u) if u.isnumeric() else u for u in arg.split(',') ]
        
def get_parser():
    parser = argparse.ArgumentParser(description='rtm12 demo')
    parser.add_argument('--trg', default="soft,soft,soft", type=list_of_values,
                        help="trg start,b1,b2 soft|wrt=value")
    parser.add_argument('--rtm12', default="33000,99000", type=list_of_values,
                        help="rtm12 b1_len, b2_len")
    parser.add_argument('--plot', default=None, type=list_of_values,
                        help="plot channel results")
    
    parser.add_argument('--trg_sync_out', default=1, type=int,
                        help="Output d1 trg to HDMI")
    parser.add_argument('--trg_wait', default=0, type=int,
                        help="Wait for keypress before each trigger")
    
    parser.add_argument('uut', nargs=1, help="uut") 
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
