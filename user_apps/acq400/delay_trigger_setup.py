#!/usr/bin/python
"""
 This file is a setup file for the delay trigger 
 mode of operation for the acq1001+480 setup. 
 This file will perform all the setup required to 
 take data on the acq480, triggering from the gpgs,
 which itself triggers from an external trigger. 
 For more information on the setup please refer to the 
 D-TACQ delay trigger report.  

 An example command line example would be: 
 
 python delay_trigger_setup.py --verbose 1 --delay 10000000 acq1001_105
 
 This command runs the script in verbose mode, 
 configures the gpg to run with a 10s delay (dependant
 on FPCLK frequency) on acq1001_105. 
"""

from __future__ import print_function
import acq400_hapi
import argparse



def configure_uut(args, uut):

	# configure uuts
	if args.verbose:
		print("Configuring UUT")

	# Run delay_trigger shell script
	uut.s0.delay_trigger = args.delay      # Run delay_trigger with parameter args.delay

	uut.s0.SYS_CLK_FPMUX = "FPCLK"          # set to front panel clk
	uut.s0.SIG_CLK_MB_FIN = 1E6             # set the clk mb fin to 1E6
	uut.s0.SIG_CLK_MB_SET = 5E7             # MB set to 5E7
	
	uut.s1.CLK = 1                          # set site 1 clk to external
	uut.s1.CLK_DX = 1                       # set site 1 clk to d0
	uut.s1.CLK_SENSE = 1                    # set site 1 clk to rising edge

	uut.s1.TRG = 1                          # set site 1 capture trg to external
	uut.s1.TRG_DX = 1                       # set site 1 trg to d1
	uut.s1.TRG_SENSE = 1                    # set site 1 trg on rising edge

	uut.s0.SIG_SYNC_OUT_CLK = 0             # set SYNC out clk to clk
	uut.s0.SIG_SYNC_OUT_CLK_DX = 0          # set SYNC clk out from d0
	uut.s0.SIG_SYNC_OUT_TRG = 0             # set SYNC out trg to trg
	uut.s0.SIG_SYNC_OUT_TRG_DX = 0          # set SYNC trg out from d0
	uut.s0.SIG_SYNC_OUT_SYNC = 0            # set SYNC out sync to gpg 
	uut.s0.SIG_SYNC_OUT_SYNC_DX = 0         # set SYNC out sync from d1

	uut.s0.transient = "PRE=%d POST=%d SOFT_TRIGGER=0" % (args.pre, args.post)
	uut.s0.set_arm = 1

	if args.verbose:
		print("Configured UUT")




def setup(args):

	# Connect to the UUT
	if args.verbose:
		print("The following UUT has been loaded: ", args.uuts)

	uuts = [acq400_hapi.Acq400(u) for u in args.uuts]

	if args.verbose:
	    print("Setting Delay Trigger as :", args.delay)

        for uut in uuts:
	    configure_uut(args, uut)

	if args.verbose:
		print("")
		print("Finished configuration")
		print("")



def run_main():
    parser = argparse.ArgumentParser(description='delay-trigger analysis')
    parser.add_argument('--verbose', type=int, default=0, help="verbose")
    parser.add_argument('--delay', type=int, default=0, help="delay_trigger parameter")
    parser.add_argument('--pre', type=int, default=0, help="delay_trigger parameter")
    parser.add_argument('--post', type=int, default=100000, help="delay_trigger parameter")
    parser.add_argument('uuts', nargs='+', help="uut names")
    setup(parser.parse_args())
    


if __name__  == '__main__':
    run_main()

