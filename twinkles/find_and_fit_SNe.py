# find objectIds for all deblended sources with chisq > 1e4
# Get light curves for each source
#    select sources where the target quantile value is below some threshold
#       e.g., 95%-tile value < 0.2*peak_flux, and more than one flux point
#       is above that flux threshold.
# For SN candidate:
#    select a +/- 30 day window around the peak flux and fit the
#    salt2-extended model.
from __future__ import print_function
from collections import OrderedDict
import numpy as np
import astropy.time
import matplotlib.pyplot as plt
import sncosmo
from desc.pserv import DbConnection
import desc.monitor
from light_curve_service import LightCurveFactory
from find_peaks import find_peaks
plt.ion()

__all__ = ['L2DataService']

def get_nparray(cursor):
    return np.array([x[0] for x in cursor])

class L2DataService(desc.monitor.Level2DataService):
    def __init__(self, repo=None, db_info=None):
        super(L2DataService, self).__init__(repo=repo, db_info=db_info)
        self._get_mjds()

    def _get_mjds(self):
        self.mjds = dict()
        for band in 'ugrizy':
            query = """select obsStart from CcdVisit where
                       filterName='%(band)s' order by obsStart asc""" % locals()
            self.mjds[band] =\
                astropy.time.Time(self.conn.apply(query, get_nparray)).mjd

    def get_objectIds(self, band, chisq_min):
        dof = len(self.mjds[band]) - 1
        query = """select cs.objectId from Chisq cs
                   join Object obj on cs.objectId=obj.objectId
                   join ObjectNumChildren numCh on obj.objectId=numCh.objectId
                   where cs.filterName='%(band)s' and cs.dof=%(dof)i
                   and cs.chisq > %(chisq_min)s
                   and numCh.numChildren=0""" % locals()
        return self.conn.apply(query, get_nparray)

    def get_SN_candidate_lcs(self, band, chisq_min, threshold=0.2, frac=0.95):
        query_tpl = """select fs.psFlux, fs.ccdVisitId
                       from ForcedSource fs join CcdVisit cv
                       on fs.ccdVisitId=cv.ccdVisitId
                       where fs.objectId=%(objectId)i and
                       cv.filterName='%(band)s' and fs.psFlux_Sigma!=0
                       order by fs.ccdVisitId asc"""
        dof = len(self.mjds[band]) - 1
        lcs = OrderedDict()
        objectIds = self.get_objectIds(band, chisq_min)
        for objectId in objectIds:
            lc = self.conn.apply(query_tpl % locals(),  get_nparray)
            # Find number of light curve fluxes that are above threshold.
            above_threshold = len(np.where(lc < threshold*max(lc))[0])
            # Check if there are at least frac*len(lc) fluxes
            # measurements are above threshold
            if above_threshold > frac*len(lc) and above_threshold < dof - 1:
                lcs[objectId] = lc
        return lcs

# Find objectIds for all deblended sources that have chi-square values
# (for their u band light curves) above chisq_min.
if __name__ == '__main__':
    db_info = dict(database='jc_desc',
                   host='ki-sr01.slac.stanford.edu',
                   port=3307)

    l2_service = L2DataService(db_info=db_info)
    lc_factory = LightCurveFactory(**db_info)

    band = 'r'
    chisq_min = 1e4

    lcs = l2_service.get_SN_candidate_lcs(band, chisq_min)
    mjds = l2_service.mjds[band]

    print("# SNe candidates:", len(lcs))

    # Define a +/-30 day window around the peak flux.
    dt = 30

    outfile = 'tmp.txt'
    with open(outfile, 'w') as output:
        output.write('#objectId  chisq  ndof  z  t0  x0  x1  c\n')
        for objectId, fluxes in lcs.items()[:5]:
            peak_indexes = find_peaks(fluxes)[0][0]
            lc = lc_factory.create(objectId)
            for ipeak in peak_indexes:
                print("fitting object %i, peak index %i" % (objectId, ipeak))
                mjd_peak = mjds[ipeak]
                mask = np.where((lc.data['mjd'] > mjd_peak - dt)
                                & (lc.data['mjd'] < mjd_peak + dt)
                                & (lc.data['bandpass'] != 'lsstu'))
                sn_data = lc.data[mask]
                model = sncosmo.Model(source='salt2-extended')
                model.set(t0=mjd_peak, z=0.2)
                try:
                    res, fitted_model =\
                        sncosmo.fit_lc(sn_data, model, 'z t0 x0 x1 c'.split(),
                                       bounds=dict(z=(0.01, 1.)))
                except (RuntimeError, sncosmo.fitting.DataQualityError):
                    continue
                if res.success:
                    output.write('%i  ' % objectId)
                    output.write('%.2e  ' % res.chisq)
                    output.write('%i  ' % res.ndof)
                    for item in res.parameters:
                        output.write('%s  ' % item)
                    output.write('\n')
                    output.flush()
