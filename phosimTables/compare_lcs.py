"""
Compare light curves from Stack Level 2 analysis of PhoSim data to the
input CatSim light curves.
"""
from __future__ import print_function
import os
import pandas as pd
import matplotlib.pyplot as plt
from PhosimDbInterface import PhosimObjects
import lsst.sims.photUtils as sims_photUtils
import lsst.utils
from desc.monitor import LightCurve, RefLightCurves
plt.ion()

class LightCurveComparer(object):
    """
    Class to overlay MC and measured light curves for the LSST bands.
    """
    def __init__(self, nx=3, ny=2, figsize=(15, 10), twinkles_db_info=None):
        """
        Set up the light curve comparer class.
        """
        self.nx, self.ny = nx, ny
        plt.rcParams['figure.figsize'] = figsize
        self.fig = None

        if twinkles_db_info is None:
            self.twinkles_db_info = dict()
        else:
            self.twinkles_db_info = twinkles_db_info

        # Get the SN-like objects from the Phosim db tables.
        self.SNs = PhosimObjects(dof_range=(0, 30), chisq_range=(1e3, 1e10))

        # Set up the reference light curve server.
        self.idSequence = self.SNs.data['sourceId'].tolist()
        obs = pd.read_csv(os.path.join(lsst.utils.getPackageDir('monitor'),
                                       'data', 'SelectedKrakenVisits.csv'),
                          index_col='obsHistID')[['expMJD', 'filter',
                                                  'fiveSigmaDepth']]
        bp_dict = sims_photUtils.BandpassDict.loadBandpassesFromFiles()[0]
        self.ref_lc_server = RefLightCurves(idSequence=self.idSequence,
                                            tableName='TwinkSN',
                                            bandPassDict=bp_dict,
                                            observations=obs)
    def plot_bands(self, sourceId):
        "Plot all LSST bands."
        for i, band in enumerate('ugrizy'):
            self.plot_band(i, sourceId, band)

    def plot_band(self, i, sourceId, band):
        """
        Plot light curves for aa single LSST band.
        """
        if i % (self.nx*self.ny) == 0 or self.fig is None:
            self.fig = plt.figure()
        ref_lc = self.ref_lc_server.lightCurve(sourceId, band)
        self.fig.add_subplot(*(self.ny, self.nx, (i % (self.nx*self.ny)) + 1))
        plt.errorbar(ref_lc['time'], ref_lc['flux']*1e9,
                     yerr=(ref_lc['fluxerr']*1e9).tolist(),
                     fmt=':.')
        xaxis_range = plt.axis()[:2]
        plt.annotate('sourceId: %s' % sourceId,
                     (0.05, 0.9), xycoords='axes fraction', size='small',
                     color='blue')

        # Find the objectId of the nearest coadd object and its separation
        # from the Phosim object.
        objectId, sep = self.SNs.find_nearest_coadd_object(sourceId)
        lc = LightCurve()
        self.twinkles_db_info['objid'] = objectId
        lc.build_lightcurve_from_db(**self.twinkles_db_info)
        df = lc.lightcurve.to_pandas()

        selection = df['bandpass'] == 'lsst%(band)s' % locals()
        plt.errorbar(df[selection]['mjd'], df[selection]['flux'],
                     yerr=df[selection]['flux_error'].tolist(),
                     color='red', fmt='--.')

        axis_range = list(plt.axis())
        # Fix the x-axis to the reference light curve abscissa range.
        axis_range[:2] = xaxis_range
        # Add some vertical space in plot for the object id annotation.
        axis_range[-1] *= 1.2
        plt.axis(axis_range)
        plt.xlabel('MJD')
        plt.ylabel('flux (nmagy)')
        plt.title('%(band)s band' % locals())
        plt.annotate('objectId: %s\noffset: %.2f arcsec'%(objectId, sep.arcsec),
                     (0.05, 0.85), xycoords='axes fraction', size='small',
                     color='red', verticalalignment='top')

if __name__ == '__main__':
    db_info = dict(database='jc_desc',
                   host='ki-sr01.slac.stanford.edu',
                   port=3307)

    lc_comparer = LightCurveComparer(twinkles_db_info=db_info)
    for i, sourceId in enumerate(lc_comparer.idSequence[:10]):
        print("processing", i, sourceId)
        lc_comparer.plot_bands(sourceId)
        plt.savefig('%i_lcs.png' % sourceId)
