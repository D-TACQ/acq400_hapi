import matplotlib.pyplot as plt

WAVE_CMDS = {}

def ui(parser, cmd_args=None):
    parser.add_argument('--root', default="./", help='root directory, default ./')
    parser.add_argument('--ch', default='1', help='channel number')
    if cmd_args is not None and len(cmd_args) != 0 and cmd_args[0] == '--help':
        parser.print_help()
        return None
    elif cmd_args is not None and len(cmd_args) != 0 and cmd_args[0] == '--usage':
        parser.print_usage()
        return None 
    else:
        return parser.parse_args(cmd_args)
    
def plot(data, title):
    plt.title(title)
    plt.plot(data)
    plt.show()