import glob
import time
import pandas as pd
import pylab_plotter as plot
plot.pylab.ion()

ccdVisit = pd.read_pickle('ccdVisit.pkl')
object_table = pd.read_pickle('object_table.pkl')

class ForcedSourceData(object):
    def __init__(self, forced_files):
        self.files = forced_files
    def __call__(self, objectId, band=None):
        for i, item in enumerate(self.files):
            print i, item
            forced = pd.read_pickle(item)
            lc_data = forced.merge(ccdVisit, on='ccdVisitId')
            selection = (lc_data['objectId'] == objectId)
            if band is not None:
                selection = selection & (lc_data['filterName'] == band)
            if i == 0:
                df = lc_data[selection]
            else:
                df = df.append(lc_data[selection])
        return df

forced_files = sorted(glob.glob('forced*.pkl'))

t0 = time.time()
forced_data = ForcedSourceData(forced_files)
t1 = time.time()
df = forced_data(1628)
t2 = time.time()

print 'execution times:', t2 - t1

mjd = df['obsStart']
flux = df['psFlux']
fluxerr = df['psFlux_Sigma']

print len(mjd)

plot.xyplot(mjd, flux, yerr=fluxerr, xname='mjd', yname='flux')
