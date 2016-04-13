"""
This needs to be run in a bash environment where 
$ setup obs_lsstSim
$ setup -m none -r and_files astrometry_net_data
have been run and which contains an images/ and and_files/ 
subdirectories.
"""

import subprocess

visit_list = range(840, 849)
visit = '^'.join([str(x) for x in visit_list])
input = 'input_data'
output = 'output_data'
filter = 'r'
sensor = '1,1'
raft = '2,2'
coadd_id = 'filter=%(filter)s patch=0,0 tract=0' % locals()

command_templates = [
    'ingestImages.py images images/lsst_*.fits.gz --mode link --output %(input)s',
    'processEimage.py %(input)s/ --id visit=%(visit)s --output %(output)s',
    'makeDiscreteSkyMap.py %(output)s/ --id visit=%(visit)s',
    'makeCoaddTempExp.py %(output)s/ --selectId visit=%(visit)s --id %(coadd_id)s --config bgSubtracted=True',
    'assembleCoadd.py %(output)s/ --selectId visit=%(visit)s --id %(coadd_id)s --config doInterp=True',
    'detectCoaddSources.py %(output)s/ --id %(coadd_id)s',
    'mergeCoaddDetections.py %(output)s/ --id %(coadd_id)s',
    'measureCoaddSources.py %(output)s/ --id %(coadd_id)s',
    'mergeCoaddMeasurements.py %(output)s/ --id %(coadd_id)s',
    "forcedPhotCcd.py %(output)s/ --id tract=0 filter=%(filter)s visit=%(visit)s sensor=%(sensor)s raft=%(raft)s --config measurement.doApplyApCorr='yes'"
    ]

for item in command_templates:
    command = item % locals()
    print command
    subprocess.call(command, shell=True)
