from __future__ import print_function
import os
import pandas as pd
import matplotlib.pyplot as plt
from PhosimDbInterface import PhosimObjects
import lsst.sims.photUtils as sims_photUtils
import lsst.utils
from desc.monitor import LightCurve, RefLightCurves
plt.ion()

# Get the SN-like objects from the Phosim db tables.
SNs = PhosimObjects(dof_range=(0, 30), chisq_range=(1e3, 1e10))

# Set up the reference light curve server.
idSequence = SNs.data['sourceId'].tolist()
obs = pd.read_csv(os.path.join(lsst.utils.getPackageDir('monitor'),
                               'data', 'SelectedKrakenVisits.csv'),
                  index_col='obsHistID')[['expMJD', 'filter', 'fiveSigmaDepth']]
bp_dict = sims_photUtils.BandpassDict.loadBandpassesFromFiles()[0]
ref_lc_server = RefLightCurves(idSequence=idSequence,
                               tableName='TwinkSN',
                               bandPassDict=bp_dict,
                               observations=obs)

def plot_band(source_id, i):
    print('processing', i, sourceId)
    if i % (nx*ny) == 0:
        fig = plt.figure()
    ref_lc = ref_lc_server.lightCurve(sourceId, band)
    ax = fig.add_subplot(*(ny, nx, (i % (nx*ny))+1))
    plt.errorbar(ref_lc['time'], ref_lc['flux']*1e9,
                 yerr=(ref_lc['fluxerr']*1e9).tolist(),
                 fmt=':.')
    xaxis_range = plt.axis()[:2]
    plt.annotate('sourceId: %s' % sourceId,
                 (0.05, 0.9), xycoords='axes fraction', size='small',
                 color='blue')

    # Find the objectId of the nearest coadd object and its separation
    # from the Phosim object.
    objectId, sep = SNs.find_nearest_coadd_object(sourceId)
    lc = LightCurve()
    lc.build_lightcurve_from_db(objid=objectId, port=53306)
    df = lc.lightcurve.to_pandas()

    selection = df['bandpass'] == 'lsst%(band)s' % locals()
    plt.errorbar(df[selection]['mjd'], df[selection]['flux'],
                 yerr=df[selection]['flux_error'].tolist(),
                 color='red', fmt='--.')

    axis_range = list(plt.axis())
#    # Fix the x-axis to the reference light curve abscissa range.
    axis_range[:2] = xaxis_range
    # Add some vertical space in plot for the object id annotation.
    axis_range[-1] *= 1.2
    plt.axis(axis_range)
    if i in (6, 7, 8):
        plt.xlabel('MJD')
    if i in (0, 3, 6):
        plt.ylabel('%(band)s band flux (nmagy)' % locals())
    plt.annotate('objectId: %s\noffset: %.2farcsec' % (objectId, sep.arcsec),
                 (0.05, 0.85), xycoords='axes fraction', size='small',
                 color='red', verticalalignment='top')


nx, ny = 1, 2
plt.rcParams['figure.figsize'] = 10, 10
for band in 'ugrizy':
    for i, sourceId in enumerate(idSequence[:10]):
