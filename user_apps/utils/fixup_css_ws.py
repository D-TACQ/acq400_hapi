'''
Created on 19 Jun 2021

@author: pgm
'''
import acq400_hapi
import argparse
import os
import re
import sys

def ui():
    parser = argparse.ArgumentParser(description='acq400_remote_script') 
    parser.add_argument('-v','--verbose', default=0, help="show more info")
    parser.add_argument('--user', default=None, help="user name to change")
    parser.add_argument('--uuts', default=None, help="uuts to change [uut[1][,uut2[,uut3...]]]]")
    parser.add_argument('ws', nargs='+', help="workspace[s] to change")
    return parser.parse_args()
   

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
                text = text.replace('/home/pgm', args.user)
                
                
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
                    sub_bytes = args.user.encode()
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

          
def run_main():
    args = ui()
    #args.pat = re.compile(r'/home/pgm/')
    args.pat = re.compile('(/home/pgm)')
    args.bpat = re.compile(b'(/home/pgm)')
    for ws in args.ws:
        fixup(args, ws)
    
    


# execution starts here

if __name__ == '__main__':
    run_main()