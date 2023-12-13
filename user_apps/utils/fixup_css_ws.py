'''Fixup cs studio workspace

Created on 19 Jun 2021

@author: pgm
'''
import acq400_hapi
import argparse
import os
import re
import sys

def get_parser():
    parser = argparse.ArgumentParser(description='acq400_remote_script') 
    parser.add_argument('-v','--verbose', default=0, help="show more info")
    parser.add_argument('--olduser', default=None, help="user name to change")
    parser.add_argument('--newuser', default=None, help="user name to change")
#    parser.add_argument('--uuts', default=None, help="uuts to change [uut[1][,uut2[,uut3...]]]]")
    parser.add_argument('ws', nargs='+', help="workspace[s] to change")
    return parser
   

# ASCII ROOLS OK, BackSlash, ForwardSlash
BS = 0x5c
"""ASCII BackSlash"""

FS = 0x2f
"""ASCII ForwardSlash"""

# URI is in Unix notation, AND must have leading FS
'''
[pgm@hoy5 acq400_hapi]$ hexdump -C /home/pgm/SANDBOX/DOC-215920-01-FAT/.metadata/.plugins/org.eclipse.core.resources/.projects/ACQ400/.location
00000000  40 b1 8b 81 23 bc 00 14  1a 25 96 e7 a3 93 be 1e  |@...#....%......|
00000010  00 2d 55 52 49 2f 2f 66  69 6c 65 3a 2f 43 3a 2f  |.-URI//file:/C:/|
00000020  55 73 65 72 73 2f 70 67  6d 30 30 2f 50 52 4f 4a  |Users/pgm00/PROJ|
00000030  45 43 54 53 2f 41 43 51  34 30 30 43 53 53 2f 41  |ECTS/ACQ400CSS/A|
00000040  43 51 34 30 30 00 00 00  00 00 00 00 00 c0 58 fb  |CQ400.........X.|
00000050  f3 23 bc 00 14 1a 51 f3  8c 7b bb 77 c6           |.#....Q..{.w.|

'''

def fixup(args, ws):
    print("fixup {}".format(ws))
    for subdir, dirs, files in os.walk(ws):
        for file in files:
            path = subdir+os.sep+file
            print(path)
            file_changed = False
            wmode = None
            
            if path.endswith(".old"):
                continue
            
            try:
                with open(path, 'r') as fp:
                    text = fp.read()
                for match in re.finditer(args.pat, text):
                    print("MATCH {} start:{} end:{}".format(match, match.start(), match.end()))
                    file_changed = True
                    wmode = 'w'
                    
                if file_changed:
                    text = text.replace(args.olduser, args.newuser)
                
            except UnicodeDecodeError:
                with open(path, 'rb') as fp:
                    text = fp.read()
                
                for match in re.finditer(args.bpat, text):
                    print("Binary File match {} start:{} end:{}".format(match, match.start(), match.end()))
                    print("here is our match {}".format(text[match.start():match.end()]))
                    print("here is what's next {}".format(text[match.end():match.end()+20]))
                    trailer_start = match.end()
                    trailer_end = trailer_start+1
                    while text[trailer_end] != 0:
                        trailer_end += 1
                    headroom_end = trailer_end + 1
                    while text[headroom_end] == 0:
                        headroom_end += 1
                    print("trailer {}, headroom {}".format(text[trailer_start:trailer_end], headroom_end - trailer_end))
                    
                    sub_bytes = args.newuser.encode()
                    if len(sub_bytes) > (match.end() - match.start()) + (headroom_end - trailer_end):
                        print("ERROR: unable to fit new name {} in binary file".format(args.user))
                        sys.exit(1)
                    trailer = text[trailer_start:trailer_end]
                    cursor = match.start()
                    text = bytearray(text)
                    for b in sub_bytes:
                        text[cursor] = b
                        cursor += 1
                    for b in trailer:
                        text[cursor] = b
                        cursor += 1
                    for x in range(cursor, headroom_end):
                        text[cursor] = 0
                        cursor += 1
                    file_changed = True
                    wmode = 'wb'
            if file_changed:
                print("acting on file_changed {}".format(path))
                os.rename(path, path+".old")
                with open(path, wmode) as fp:
                    fp.write(text)

          
def run_main(args):
    #args.pat = re.compile(r'/home/pgm/')
    args.pat = re.compile('({})'.format(args.olduser))
    args.bpat = re.compile(('(' + args.olduser + ')' ).encode())
    for ws in args.ws:
        fixup(args, ws)
    
    


# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())