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
from light_curve_service import LightCurveFactory
plt.ion()

def get_nparray(cursor):
    return np.array([x[0] for x in cursor])

db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')
jc_desc = DbConnection(**db_info)
lc_factory = LightCurveFactory(**db_info)

tier1_frac = 0.95
tier1_threshold = 0.2

# Find objectIds for all deblended sources that have chi-square values
# (for their u band light curves) above chisq_min.
band = 'u'
chisq_min = 1e4

# MJD values for u band.
query = "select obsStart from CcdVisit where filterName='%(band)s'" % locals()
mjds = astropy.time.Time(jc_desc.apply(query, get_nparray)).mjd
dof = len(mjds) - 1

query = '''select cs.objectId from Chisq cs
           join Object obj on cs.objectId=obj.objectId
           join ObjectNumChildren numCh on obj.objectId=numCh.objectId
           where cs.filterName='%(band)s' and cs.dof=%(dof)i
           and cs.chisq > %(chisq_min)s
           and numCh.numChildren=0''' % locals()

object_ids = jc_desc.apply(query, get_nparray)

# Get the u band light curves for each source.
query_tpl = """select fs.psFlux, fs.ccdVisitId
            from ForcedSource fs join CcdVisit cv
            on fs.ccdVisitId=cv.ccdVisitId
            where fs.objectId=%(objectId)i and cv.filterName='%(band)s'
            and fs.psFlux_Sigma!=0
            order by fs.ccdVisitId asc"""
lcs = OrderedDict()
for objectId in object_ids:
    lc = jc_desc.apply(query_tpl % locals(),  get_nparray)
    index = np.where(lc < tier1_threshold*max(lc))
    # Check if there are at least 10 measurements above the fractional
    # tier 1 threshold.
    if (len(index[0]) > tier1_frac*len(lc)
        and len(index[0]) < dof-1):
        lcs[objectId] = lc

print("# tier 1 SNe candidates:", len(lcs))

# Define a +/-30 day window around the peak flux, and plot the lightcurves.
dt = 30
with open('run1.1_SNe_salt2-extended_fit_results.txt', 'w') as output:
    output.write('#objectId  chisq  ndof  z  t0  x0  x1  c\n')
    for object_id, fluxes in lcs.items():
        print("fitting object", object_id)
        mjd_peak = mjds[np.where(fluxes == max(fluxes))]
        lc = lc_factory.create(object_id)
        date_mask = np.where((lc.data['mjd'] > mjd_peak - dt)
                             & (lc.data['mjd'] < mjd_peak + dt))
        sn_data = lc.data[date_mask]
        model = sncosmo.Model(source='salt2-extended')
        model.set(t0=mjd_peak, z=0.2)
        try:
            res, fitted_model = sncosmo.fit_lc(sn_data, model,
                                               ['z', 't0', 'x0', 'x1', 'c'],
                                               bounds=dict(z=(0.01, 1.)))
        except RuntimeError:
            continue
        if res.success:
            output.write('%i  ' % object_id)
            output.write('%.2e  ' % res.chisq)
            output.write('%i  ' % res.ndof)
            for item in res.parameters:
                output.write('%s  ' % item)
            output.write('\n')
            output.flush()
