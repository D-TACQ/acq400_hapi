#!/bin/python3
'''
Use Product Listing Report csv to collate infor from CAL DATA
eg
./get-backup-fw.py DOC-215620-01-uuts.csv
# run this
./DOC-215620-01-uuts-full.sh

'''

import argparse
import csv
import os


def get_args():
    parser = argparse.ArgumentParser(
        description = "Use SNDB csv report to gather UUT shipping info")
    parser.add_argument('src_csv', nargs='+', default='DOC-215620-01-uuts.csv', help="source definition")
    return parser.parse_args()
        
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
        print("{} calibration not found".format(caldir))
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
                    return (fpgaversion, fields[2].rstrip())                    
                else:
                    pass
    except:
        print("{} calibration not found".format(caldir))
    return ("unknown",)  

def add_job(args, job, jobfile, ir, caldir):
    if ir == 0:
        tarf = job.replace('.sh', '.tar')
        jobfile.write("#!/bin/bash\n")        
        return
        
    try:
        xmlfiles = os.listdir("{}/local/cal".format(caldir))
        for file in xmlfiles:
            jobfile.write("cp {}/{}/{} .\n".format(caldir, "local/cal", file))
    except FileNotFoundError:
        pass

def gather(args, src):
    pfx = src.split('.')[0]
    dst = "{}-full.csv".format(pfx)
    job = "{}-full.sh".format(pfx)
    cal = "{}-cal.tar".format(pfx) 
    
    with open(dst, 'w') as dstfile, open(job, 'w') as jobfile:
        writer = csv.writer(dstfile)
        with open(src) as csvfile:
            reader = csv.reader(csvfile)
            for ir, row in enumerate(reader):
                model = 'acq1001' if row[0].startswith('CE40') \
                        else 'acq2106' if row[0].startswith('CE41') else 'unknown'
                if model == 'unknown':
                    if ir == 0:
                        row.append("ESW VERSION")
                        row.append("FPGA FILE")
                        row.append("FPGA DATE")
                    writer.writerow(row)
                    add_job(args, job, jobfile, ir, "nowhere")
                    continue
                sn = row[0][len(row[0])-3:]
                row[2] = 'xxx'
                uutname = "acq1001_{}".format(sn)
                caldir = "/home/dt100/CAL/{}_CAL/{}".format(model.upper(), uutname)
                esw_version = getEswVersion(caldir)
                fpga_version = getFpgaVersion(caldir)
                
                row.append(esw_version)
                for vx in fpga_version:
                    row.append(vx)
                writer.writerow(row)
                
                add_job(args, job, jobfile, ir, caldir)
    
                print("UUT: {} model:{} {} version:{} fpga:{}".format(row[0], model, uutname, esw_version, fpga_version))
    
                   
        jobfile.write("tar cvf {} *.xml\n".format(cal)) 
        jobfile.write("rm *.xml\n")       
        os.chmod(job, 0o777)
        print("# run this")
        print("./{}".format(job))


def main():
    args = get_args();
    for src in args.src_csv:
        gather(args, src)

if __name__ == '__main__':
    main()
