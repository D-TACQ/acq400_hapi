import numpy as np
import os

try:
    import matplotlib.pyplot as plt
    plot_ok = True
except:
    plot_ok = False

WAVE_CMDS = {}

def ui(parser, cmd_args=None):
    parser.add_argument('--reps', type=int, default=1, help='repeat pattern')
    parser.add_argument('--root', default="./", help='root directory')
    parser.add_argument('--ch', default='1', help='channel number')
    parser.add_argument('--data32', type=int, default=0, help="set 1 for 32 bit data")
    if cmd_args is not None and len(cmd_args) != 0 and cmd_args[0] == '--help':
        parser.print_help()
        return None
    elif cmd_args is not None and len(cmd_args) != 0 and cmd_args[0] == '--usage':
        parser.print_usage()
        return None 
    else:
        args = parser.parse_args(cmd_args)
        args.format = np.int16 if args.data32 == 0 else np.int32
        return args
 
def exec_command(args, command_wrapper):  
    if not args:
        return None, None
    pat = command_wrapper(args)
    data = np.zeros(0)
    for rep in range(0, args.reps):
        data = np.append(data, pat)
    
    if args.root != './':
        os.makedirs(args.root, exist_ok=True)
    if args.root[-1] == '/':
        args.root = args.root[:-1]        
    fn = str(command_wrapper)
    
    data.astype(args.format).tofile(fn)
    print(f'saved as {fn}')
    return data, fn  
  
def plot(data, title):
    if plot_ok:
        plt.title(title)
        plt.plot(data)
        plt.show()
    else:
        print("sorry plot not available on this platform")
