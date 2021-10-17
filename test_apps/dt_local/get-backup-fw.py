#!/bin/python3

import csv

def getEswVersion(caldir):
    eswversion = 'unknown'
    try:
        with open('{}/firmware_version'.format(caldir), 'r', encoding='UTF-8') as fwversion:
            for line in fwversion:
                fields = line.split(' ')
                relkey = fields[0]
                relvers = fields[1]
                if relkey == 'RELEASE':
                    eswversion = relvers.rstrip()
                    break
    except:
        print("{} calibration not found".format(uutname))
    return eswversion

def getFpgaVersion(caldir):
    fpgaversion = 'unknown'
    try:
        with open('{}/fpga'.format(caldir), 'r', encoding='UTF-8') as fpga:
            for line in fpga:
                #fields = line.split(r'[\s]+')
                fields = line.split()
                relkey = fields[0]
                if relkey == 'load.fpga':                    
                    fpgaversion = fields[2].rstrip()
                elif relkey == 'date':                    
                    return fpgaversion + ",{}".format(fields[2].rstrip())                    
                else:
                    pass
    except:
        print("{} calibration not found".format(uutname))
    return "unknown"  
  
with open('DOC-215620-01-uuts.csv') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        model = 'acq1001' if row[0].startswith('CE40') \
                else 'acq2106' if row[0].startswith('CE41') else 'unknown'
        if model == 'unknown':
            continue
        sn = row[0][len(row[0])-3:]
        uutname = "acq1001_{}".format(sn)
        caldir = "/home/dt100/CAL/{}_CAL/{}".format(model.upper(), uutname)
        esw_version = getEswVersion(caldir)
        fpga_version = getFpgaVersion(caldir)


        print("UUT: {} model:{} {} version:{} fpga:{}".format(row[0], model, uutname, esw_version, fpga_version))

#        print(",".join(row))


