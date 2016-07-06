"""
Compare light curves from Stack Level 2 analysis of PhoSim data to the
input CatSim light curves.
"""
from __future__ import print_function
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PhosimDbInterface import PhosimObjects, separation
import lsst.sims.photUtils as sims_photUtils
import lsst.utils
import desc.monitor
from desc.monitor import LightCurve, RefLightCurves, PostageStampMaker,\
    convert_image_to_hdu, render_fits_image
plt.ion()

class LightCurveComparer(object):
    """
    Class to overlay MC and measured light curves for the LSST bands.
    """
    def __init__(self, nx=3, ny=2, figsize=(15, 10), twinkles_db_info=None,
                 repo=None):
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

        self.repo = repo

        l2_service = desc.monitor.Level2DataService(db_info=twinkles_db_info)
        # Get the SN-like objects from the Phosim db tables.
        self.SNs = PhosimObjects(l2_service, dof_range=(0, 30),
                                 chisq_range=(1e3, 1e10))

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
    def get_catsim_coords(self, sourceIds):
        ras, decs = [], []
        for sourceId in sourceIds:
            catsim_info = self.ref_lc_server.get_params(sourceId)
            if len(catsim_info) == 0:
                continue
            ras.append(catsim_info['snra'].values[0])
            decs.append(catsim_info['sndec'].values[0])
        return ras, decs

    def plot_bands(self, sourceId, objectId=None):
        "Plot all LSST bands."
        for i, band in enumerate('ugrizy'):
            self.plot_band(i, sourceId, band, objectId=objectId)
        self.fig.suptitle('sourceId: %(sourceId)i' % locals())

    def plot_band(self, i, sourceId, band, objectId=None):
        """
        Plot light curves for a single LSST band.
        """
        if i % (self.nx*self.ny) == 0 or self.fig is None:
#            if self.fig is not None:
#                plt.close(self.fig)
            self.fig = plt.figure()
        ref_lc = self.ref_lc_server.lightCurve(sourceId, band)
        self.fig.add_subplot(*(self.ny, self.nx, (i % (self.nx*self.ny)) + 1))
        plt.errorbar(ref_lc['time'], ref_lc['flux']*1e9,
                     yerr=(ref_lc['fluxerr']*1e9).tolist(),
                     fmt=':.')
        xaxis_range = plt.axis()[:2]

        # Find the objectId of the nearest coadd object and its separation
        # from the Phosim object.
        if objectId is None:
            objectId, sep = self.SNs.find_nearest_coadd_object(sourceId)
        else:
            sep = separation((0, 0), (0, 0))
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
        axis_range[-1] *= 1.1
        plt.axis(axis_range)
        plt.xlabel('MJD')
        plt.ylabel('flux (nmagy)')
        plt.title('%(band)s band' % locals())
        plt.annotate('objectId: %s\noffset: %.2f arcsec'%(objectId, sep.arcsec),
                     (0.05, 0.9), xycoords='axes fraction', size='small',
                     color='red')

    def plot_postage_stamps(self, sourceId, size=10):
        ra, dec = self.get_catsim_coords((sourceId,))
        ra, dec = ra[0], dec[0]
        l2_objects = self.SNs.find_objects(ra, dec, size/2.)
        phosim_objects = self.SNs.find_phosim_objects(ra, dec, size/2.)
        snra, sndec = self.get_catsim_coords(phosim_objects['sourceId'].tolist())
        fig = plt.figure()
        for i, band in enumerate('ugrizy'):
            expfile = os.path.join(self.repo, 'deepCoadd', band, '0/0,0.fits')
            maker = PostageStampMaker(expfile)
            stamp = maker.create(ra, dec, size)
            hdu = convert_image_to_hdu(stamp)
            title = 'band: %(band)s' % locals()
            subplot = '23%i' % (i + 1)
            fig, axes, im, norm = render_fits_image(hdu, title=title, fig=fig,
                                                    subplot=subplot)
            axis_range = plt.axis()
            axes.scatter(l2_objects['RA'].tolist(),
                         l2_objects['Dec'].tolist(),
                         transform=axes.get_transform('icrs'), color='red',
                         alpha=0.5)
            axes.scatter(snra, sndec,
                         transform=axes.get_transform('icrs'),
                         color='green', alpha=0.5, marker=(5, 2), s=100)
            axes.scatter([ra], [dec],
                         transform=axes.get_transform('icrs'),
                         color='blue', alpha=0.5, marker=(5, 2), s=100)
            plt.axis(axis_range)
        fig.suptitle('sourceId: %(sourceId)i' % locals())
        return fig

if __name__ == '__main__':
    db_info = dict(database='jc_desc',
                   host='ki-sr01.slac.stanford.edu',
                   port=3307)
    repo = '/nfs/farm/g/desc/u1/users/jchiang/desc_projects/twinkles/Run1.1/output'
    lc_comparer = LightCurveComparer(twinkles_db_info=db_info, repo=repo)
#    for i, sourceId in enumerate(lc_comparer.idSequence[:10]):
#        print("processing", i, sourceId)
#        lc_comparer.plot_bands(sourceId)
#        plt.savefig('%i_lcs.png' % sourceId)
#        fig = lc_comparer.plot_postage_stamps(sourceId)
#        plt.savefig('%i_cutouts.png' % sourceId)
#        plt.close(fig)

    objectId = 3794
    ra, dec = lc_comparer.SNs.l2_service.get_coords(objectId)
    ps_objects = lc_comparer.SNs.find_phosim_objects(ra, dec, 2)
    print(ps_objects)
    for sourceId in ps_objects['sourceId']:
        if sourceId not in lc_comparer.idSequence:
            continue
        lc_comparer.plot_bands(sourceId)
        plt.savefig('%i_lcs.png' % sourceId)
        fig = lc_comparer.plot_postage_stamps(sourceId)
        plt.savefig('%i_cutouts.png' % sourceId)
        plt.close(fig)
