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

def save_VI(cfg, indent, uut):
    cfg.write('{}"{}": {}\n'.format(indent, "AI32", 66))
    
def save_VO(cfg, indent, uut):
    cfg.write('{}"{}": {}\n'.format(indent, "AO32", 66))
    
def save_config_skel(args, cfile, conns, uuts):
    indent = ''
    with open(cfile, "w") as cfg:
        cfg.write('{}{}\n'.format(indent, '{'))
        indent += '\t'
        cfg.write('{}"AFHBA": {}\n'.format(indent, '{'))
        indent += '\t'
        cfg.write('{}"UUT": [\n'.format(indent))
        indent += '\t'
        ii = 0
        for key, value in conns.items():
            cfg.write('{}{}\n'.format(indent, '{'))
            indent += '\t'          
            cfg.write('{}"DEVNUM": {},\n'.format(indent, value.dev))
            cfg.write('{}"name": "{}"\n'.format(indent, value.uut))
            cfg.write('{}"type": "pcs"\n'.format(indent))
            cfg.write('{}"sync_role": "{}\n'.format(indent, "master" if ii==0 else "slave"))
            
            cfg.write('{}"VI": {}\n'.format(indent, '{'))
            indent += '\t'
            save_VI(cfg, indent, uuts[ii])            
            indent = indent[:-1]
            cfg.write('{}{}\n'.format(indent, '},'))
            cfg.write('{}"VO": {}\n'.format(indent, '{'))
            indent += '\t'
            save_VO(cfg, indent, uuts[ii]) 
            indent = indent[:-1]
            cfg.write('{}{}\n'.format(indent, '}'))            
            
            indent = indent[:-1]
            cfg.write('{}{}{}\n'.format(indent, '}', ',' if ii < len(uuts)-1 else ''))
            ii += 1
            
        indent = indent[:-1]
        cfg.write('{}]\n'.format(indent))
        indent = indent[:-1]
        cfg.write('{}{}\n'.format(indent, '}'))
        indent = indent[:-1]
        cfg.write('{}{}\n'.format(indent, '}'))
            
            
            
        
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
            
    if args.save_config_skel:
        save_config_skel(args, args.save_config_skel, conns, uuts)

    
def run_main():
    parser = argparse.ArgumentParser(description='list all attached acq2x06 devices')
    parser.add_argument('--save_config_skel', default=None, help='save configuration skeleton')
    parser.add_argument('--verbose', default=0, type=int, help='increase verbosity')
    
    lsafhba(parser.parse_args())
    
    
    
if __name__ == '__main__':
    run_main()