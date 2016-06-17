from __future__ import print_function
from warnings import filterwarnings
import pandas as pd
import numpy as np
import astropy.time
import astropy.coordinates as coords
import astropy.units as units
import matplotlib.pyplot as plt
import MySQLdb as Database
import lsst.afw.math as afwMath
import desc.pserv

plt.ion()
filterwarnings('ignore', category=Database.Warning)

def separation(a, b):
    a_coord = coords.SkyCoord(a[0], a[1], unit=(units.degree, units.degree))
    b_coord = coords.SkyCoord(b[0], b[1], unit=(units.degree, units.degree))
    return a_coord.separation(b_coord)

class GetData(object):
    def __init__(self, columns):
        self.columns = columns
    def __call__(self, curs):
        return pd.DataFrame(data=[x for x in curs], columns=self.columns)

class PhosimObjects(object):
    def __init__(self, conn=None, dof_range=None, chisq_range=None,
                 x_range=(100, 3950), y_range=(100, 3950)):
        """
        Initialize with the PhoSim objects satisfying the search
        constraints.
        """
        if conn is None:
            self.conn = desc.pserv.DbConnection(db='jc_desc',
                                                read_default_file='~/.my.cnf')
        else:
            self.conn = conn
        if dof_range is None:
            dof_range = 0, 1000
        if chisq_range is None:
            chisq_range = 0, 1e10

        query = """select po.sourceId, lcstats.dof, lcstats.chisq,
                   po.Ra, po.Decl from PhosimObject po join
                   PhosimLightCurveStats lcstats on po.sourceId=lcstats.sourceId
                   where """
        query += "%e <= lcstats.dof and lcstats.dof <= %e " % dof_range
        query += "and %e < lcstats.chisq and lcstats.chisq < %e " % chisq_range
        query += "and lcstats.xmin > %e and lcstats.xmax < %e " % x_range
        query += "and lcstats.ymin > %e and lcstats.ymax < %e " % y_range
        query += "order by lcstats.chisq desc"
        columns = 'sourceId dof chisq RA Dec'.split()
        self.data = self.conn.apply(query, GetData(columns))

    def find_nearest_coadd_object(self, sourceId, box_size=5):
        """
        Find the nearest coadd object, searching within a box of
        box_size arcmin squared centered on the target's sky location.
        Return its objectId from the Object table.
        """
        # Get the sky coordinates of the phosim object via its sourceId.
        selection = self.data['sourceId'] == sourceId
        ra = self.data[selection]['RA']
        dec = self.data[selection]['Dec']
        # Query for objects within the box from the Object table.
        size = box_size/3600.  # convert from arcsec to degrees
        cos_dec = np.abs(np.cos(dec*np.pi/180.))
        ra_min, ra_max = ra - size/cos_dec, ra + size/cos_dec
        dec_min, dec_max = dec - size, dec + size
        query = '''select objectId, psRa, psDecl from Object obj where
                   %(ra_min)12.8f < psRa and psRa < %(ra_max)12.8f and
                   %(dec_min)12.8f < psDecl and psDecl < %(dec_max)12.8f''' \
            % locals()
        objects = self.conn.apply(query, GetData('objectId RA Dec'.split()))
        # Loop over the objects and find the closest one.
        sep_min = None
        closest = None
        for j in range(len(objects)):
            sep = separation((ra, dec), (objects['RA'][j], objects['Dec'][j]))
            if closest is None or sep < sep_min:
                sep_min = sep
                closest = j
        return objects['objectId'][closest]

    def plot_lcs(self, sourceId, band, box_size=5, verbose=False,
                 figsize=(6, 10)):
        """
        Compare the phosim counts light curves to the forced source
        lightcurves.
        """
        if sourceId not in self.data['sourceId'].tolist():
            raise RuntimeError("sourceId %i not found", sourceId)

        plt.rcParams['figure.figsize'] = figsize

        # Plot the PhoSim light curve.
        query = """select cv.obsStart, pcc.numPhotons from
                   PhosimCentroidCounts pcc join CcdVisit cv
                   on pcc.ccdVisitId=cv.ccdVisitId where
                   sourceId=%(sourceId)s and cv.filterName='%(band)s'""" \
            % locals()
        data = self.conn.apply(query, GetData('obsStart numPhot'.split()))
        mjd = astropy.time.Time(np.array(data['obsStart'].tolist())).mjd
        fig = plt.figure()
        ax = fig.add_subplot(311)
        plt.errorbar(mjd, data['numPhot'], yerr=np.sqrt(data['numPhot']),
                     fmt='o')
        xaxis_range = plt.axis()[:2]
        plt.xlabel('mjd')
        plt.ylabel('numPhotons')
        plt.annotate("sourceId: %s" % sourceId, (0.05, 0.9),
                     xycoords='axes fraction', size='small',
                     horizontalalignment='left')

        # Plot the ForcedSource light curve for the nearest coadd object.
        objectId = self.find_nearest_coadd_object(sourceId)
        query = """select cv.obsStart, fs.psFlux, fs.psFlux_Sigma
                   from CcdVisit cv join ForcedSource fs
                   on cv.ccdVisitId=fs.ccdVisitId
                   where cv.filterName='%(band)s' and fs.objectId=%(objectId)i
                   order by cv.obsStart asc""" % locals()
        l2 = self.conn.apply(query, GetData('obsStart flux fluxerr'.split()))
        l2_mjd = astropy.time.Time(np.array(l2['obsStart'].tolist())).mjd
        ax = fig.add_subplot(312)
        plt.errorbar(l2_mjd, l2['flux'], yerr=l2['fluxerr'], fmt='o')
        axis_range = list(plt.axis())
        axis_range[:2] = xaxis_range
        plt.axis(axis_range)
        plt.xlabel('mjd')
        plt.ylabel('%(band)s band flux' % locals())
        plt.annotate("objectId: %s" % objectId, (0.05, 0.9),
                     xycoords='axes fraction', size='small',
                     horizontalalignment='left')

        # Plot ratio of phosim values and baseline-subtracted L2 fluxes.
        times = []
        ratios = []
        errors = []
        for time, nphot in zip(mjd, data['numPhot'].tolist()):
            try:
                index = l2_mjd.tolist().index(time)
                flux = l2['flux'][index]
                fluxerr = l2['fluxerr'][index]
                ratio = nphot/flux
                error = ratio*np.sqrt((fluxerr/flux)**2 + 1./nphot)
                times.append(time)
                ratios.append(ratio)
                errors.append(error)
            except ValueError:
                pass
        ax = fig.add_subplot(313)
        ax.set_yscale('log', nonposy='clip')
        plt.errorbar(times, ratios, fmt='o')
        axis_range = list(plt.axis())
        axis_range[:2] = xaxis_range
        plt.axis(axis_range)
        plt.xlabel('mjd')
        plt.ylabel('numPhotons / %(band)s band flux' % locals())

if __name__ == '__main__':
    SN_objects = PhosimObjects(dof_range=(0, 30), chisq_range=(1e3, 1e10))
    AGN_objects = PhosimObjects(dof_range=(249, 249), chisq_range=(1e3, 1e10))

    band = 'r'

    sourceIds = (6144007055260714, 6145673903924266)
#    for sourceId in SN_objects.data['sourceId'].tolist()[:2]:
    for sourceId in sourceIds:
        print(sourceId)
        SN_objects.plot_lcs(sourceId, band)

#    for sourceId in AGN_objects.data['sourceId'].tolist()[:1]:
#        print(sourceId)
#        AGN_objects.plot_lcs(sourceId, band)
