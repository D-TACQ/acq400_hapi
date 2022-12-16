

import os


class PR_MONO:
    def Red(skk): print("{}".format(skk))
    def Green(skk): print("{}".format(skk)) 
    def Yellow(skk): print("{}".format(skk)) 
    def Purple(skk): print("{}".format(skk)) 
    def Cyan(skk): print("{}".format(skk)) 
    def Blue(skk): print("{}".format(skk))  
     
class PR_COLOUR:
    def Red(skk): print("\033[91m{}\033[00m".format(skk))
    def Green(skk): print("\033[92m{}\033[00m".format(skk)) 
    def Yellow(skk): print("\033[93m{}\033[00m".format(skk)) 
    def Purple(skk): print("\033[95m{}\033[00m".format(skk)) 
    def Cyan(skk): print("\033[96m{}\033[00m".format(skk)) 
    def Blue(skk): print("\033[94m{}\033[00m".format(skk))    


PR = PR_COLOUR if int(os.getenv("HAPI_COLOUR", "1")) else PR_MONO
