#!/bin/python3

import csv

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
            pass

        print("UUT: {} model:{} {} caldir {} version:{}".format(row[0], model, uutname, caldir, eswversion))

#        print(",".join(row))


