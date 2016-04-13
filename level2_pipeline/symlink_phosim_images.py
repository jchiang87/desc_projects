#!/usr/bin/env python
import subprocess

phosim_output = '/nfs/farm/g/desc/u1/Pipeline-tasks/Twinkles-phoSim/phosim_output'

command = 'find %(phosim_output)s -name lsst_[ae]_\*.fits.gz -print' % locals()
eimages = subprocess.check_output(command, shell=True).split()
for eimage in eimages:
    command = 'ln -s %(eimage)s .' % locals()
    subprocess.call(command, shell=True)

