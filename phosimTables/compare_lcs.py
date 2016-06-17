from __future__ import print_function
import matplotlib.pyplot as plt
from PhosimDbInterface import PhosimObjects
from RefLightCurveServer import RefLightCurveServer
from desc.monitor import LightCurve
plt.ion()

# Get the SN-like objects from the Phosim db tables.
SNs = PhosimObjects(dof_range=(0, 30), chisq_range=(1e3, 1e10))

# Set up the reference light curve server.
idSequence = SNs.data['sourceId'].tolist()
ref_server = RefLightCurveServer(idSequence)

plt.rcParams['figure.figsize'] = 10, 10
band = 'r'
fig = plt.figure()
for i, sourceId in enumerate(idSequence[:9]):
    print('processing ', i, sourceId)
    ref_lc = ref_server.lightCurve(sourceId, band)
    ax = fig.add_subplot(*(3, 3, i+1))
    plt.errorbar(ref_lc['time'], ref_lc['flux']*1e9,
                 yerr=(ref_lc['fluxerr']*1e9).tolist(),
                 fmt='.')
    xaxis_range = plt.axis()[:2]
    plt.annotate('sourceId: %s' % sourceId,
                 (0.05, 0.9), xycoords='axes fraction', size='small',
                 color='blue')

    # Find the objectId of the nearest coadd object.
    objectId = SNs.find_nearest_coadd_object(sourceId)
    lc = LightCurve()
    lc.build_lightcurve_from_db(objid=objectId, port=53306)
    df = lc.lightcurve.to_pandas()

    selection = df['bandpass'] == 'lsst%(band)s' % locals()
    plt.errorbar(df[selection]['mjd'], df[selection]['flux'],
                 yerr=df[selection]['flux_error'].tolist(),
                 color='red', fmt='.')

    axis_range = list(plt.axis())
    axis_range[:2] = xaxis_range
    plt.axis(axis_range)
    if i in (6, 7, 8):
        plt.xlabel('MJD')
    if i in (0, 3, 6):
        plt.ylabel('%(band)s band flux (nmagy)' % locals())
    plt.annotate('objectId: %s' % objectId,
                 (0.05, 0.85), xycoords='axes fraction', size='small',
                 color='red')
