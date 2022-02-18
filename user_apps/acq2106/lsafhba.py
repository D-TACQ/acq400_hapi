'''
lsafhba : list all afhba connections
Created on 18 Feb 2022

@author: pgm
'''

import argparse
import acq400_hapi


def mtype(mod):
#    print("is_adc:{}".format(mod.is_adc))
    mt = "none"
    if mod.is_adc.split(" ")[0]=='1':
        mt = "AI"
    elif mod.MTYPE[0] == '4':
        mt = "AO"
    elif mod.MTYPE[0] == '6':
        mt = "DI"
    else:
        mt = "UN"
    return "{}{}".format(mt, 32 if mod.data32=='1' else 16)

def lsafhba(args):
    conns = acq400_hapi.afhba404.get_connections()
    uuts = []
    
    for key, value in conns.items():
       print("{} {}".format(key, value))
       if args.verbose == 0:
           continue
       uut = acq400_hapi.factory(value.uut)
       uuts.append(uut)                 
       sites = uut.sites
       print("\tpayload:{}".format(sites))
       for s in [int(s) for s in sites]:
            print("\t\tsite:{} MODULE {} {} {}".format(\
                 s, uut.modules[s].MODEL.split(" ")[0], \
                 mtype(uut.modules[s]), uut.modules[s].NCHAN))

    
def run_main():
    parser = argparse.ArgumentParser(description='list all attached acq2x06 devices')
    parser.add_argument('--verbose', default=0, type=int, help='increase verbosity')
    
    lsafhba(parser.parse_args())
    
    
    
if __name__ == '__main__':
    run_main()