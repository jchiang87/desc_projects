from __future__ import print_function
import os
import sys
import glob
import gzip
import csv
import subprocess
from warnings import filterwarnings
import MySQLdb as Database
import numpy as np
import desc.pserv

filterwarnings('ignore', category=Database.Warning)

class Sources(dict):
    def __init__(self, csv_file):
        super(Sources, self).__init__()
        self.csv_output = open(csv_file, 'w')
        self.writer = csv.writer(self.csv_output, delimiter=',')
        self.writer.writerow('sourceId Ra Decl'.split())

    def __del__(self):
        self.csv_output.close()

    def process_object_line(self, line):
        if not line.startswith('object'):
            return
        tokens = line.split()
        if self.has_key(tokens[1]):
            return
        self[tokens[1]] = tokens[2:4]
        self.writer.writerow(tokens[1:4])

def make_object_csv_file(object_file, instcats):
    my_sources = Sources(object_file)

    for i, item in enumerate(instcats):
        print("processing file:", i, os.path.basename(item))
        with gzip.open(item, 'rb') as input:
            for line in input:
                my_sources.process_object_line(line)
        print("  current number of objects", len(my_sources))
        my_sources.csv_output.flush()
        sys.stdout.flush()
    return my_sources

def make_centroid_csv_file(centroid_file, outfile='centroid_file.csv'):
    ccdVisitId = os.path.basename(centroid_file).split('_')[3]
    with open(outfile, 'w') as output:
        writer = csv.writer(output, delimiter=',')
        writer.writerow('sourceId ccdVisitId numPhotons avgX avgY'.split())
        with open(centroid_file) as input_:
            for line in input_:
                if line.startswith('SourceID'):
                    continue
                tokens = line.split()
                if (tokens[2].find('nan') != -1 or tokens[3].find('nan') != -1
                    or tokens[0].startswith('0.000000')):
                    continue
                row = [tokens[0].split('.')[0], ccdVisitId]
                row.extend(tokens[1:4])
                writer.writerow(row)
    return outfile

if __name__ == '__main__':
    dry_run = False

#    instcat_dir = '/nfs/farm/g/desc/u1/data/Twinkles/phoSim/Run1_InstCats_SEDs'
#    instcats = sorted(glob.glob(os.path.join(instcat_dir,
#                                             'phosim_input_*.txt.gz')))
#
#    # csv file and load into the PhosimObject table.
#    object_file = 'phosim_object_file.csv'
#    make_object_csv_file(object_file, instcats)

    connect = desc.pserv.DbConnection(db='jc_desc',
                                      read_default_file='~/.my.cnf')

#    connect.run_script('create_PhosimObject.sql', dry_run=dry_run)
#    connect.load_csv('PhosimObject', object_file)

#    connect.run_script('create_PhosimCentroidCounts.sql', dry_run=dry_run)

    centroid_files_dir = '/nfs/farm/g/desc/u1/Pipeline-tasks/Twinkles-phoSim1sx/phosim_output'

    command = ('find %s -name centroid_lsst_e_\*_R22_S11_E000.txt -print'
               % centroid_files_dir)
    centroid_files = sorted(subprocess.check_output(command, shell=True).split('\n'))
    for item in centroid_files[3:]:
        if not os.path.isfile(item):
            continue
        print('procesing:', item)
        sys.stdout.flush()
        csv_file = make_centroid_csv_file(item)
        connect.load_csv('PhosimCentroidCounts', csv_file)
        os.remove(csv_file)
