#!/usr/bin/env python
"""
This needs to be run in a bash environment where
$ setup obs_lsstSim
$ setup -m none -r and_files astrometry_net_data
have been run and which contains an images/ and and_files/
subdirectories.
"""
import os
import sys
import subprocess

def find_visits(image_repo):
    command = 'find %(image_repo)s -name lsst_e\* -print' % locals()
    subdirs = subprocess.check_output(command, shell=True).split()
    visit_list = []
    for item in subdirs:
        visit_list.append(int(os.path.basename(item).split('_')[2]))
    return visit_list

visit_list = find_visits('images')
print visit_list

visit = '^'.join([str(x) for x in visit_list])
input = 'input_data'
output = 'output_data'
sensor = '1,1'
raft = '2,2'
coadd_id = lambda filt : 'filter=%s patch=0,0 tract=0' % filt

command_templates = [
    'ingestImages.py images images/lsst_*.fits.gz --mode link --output %(input)s',
    'processEimage.py %(input)s/ --id visit=%(visit)s --output %(output)s',
    'makeDiscreteSkyMap.py %(output)s/ --id visit=%(visit)s --output %(output)s',
    ]

command_templates.extend(
    [('makeCoaddTempExp.py %(output)s/ --selectId visit=%(visit)s --id '
      + coadd_id(filt) + ' --config bgSubtracted=True --output %(output)s')
     for filt in 'ugrizy']
    )

command_templates.extend(
    [('assembleCoadd.py %(output)s/ --selectId visit=%(visit)s --id '
      + coadd_id(filt) + ' --config doInterp=True --output %(output)s') % locals()
     for filt in 'ugrizy']
    )

my_coadd_id = coadd_id('^'.join('ugrizy'))
command_templates.extend(
    [
    'detectCoaddSources.py %(output)s/ --id %(my_coadd_id)s --output %(output)s',
    'mergeCoaddDetections.py %(output)s/ --id %(my_coadd_id)s --output %(output)s',
    'measureCoaddSources.py %(output)s/ --id %(my_coadd_id)s --output %(output)s',
    'mergeCoaddMeasurements.py %(output)s/ --id %(my_coadd_id)s --output %(output)s',
    "forcedPhotCcd.py %(output)s/ --id tract=0 visit=%(visit)s sensor=%(sensor)s raft=%(raft)s --config measurement.doApplyApCorr='yes' --output %(output)s"
    ]
    )

for item in command_templates:
    command = item % locals()
    print command
    sys.stdout.flush()
    subprocess.call(command, shell=True)
