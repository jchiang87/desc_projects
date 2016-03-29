import os
import sys
from collections import OrderedDict
import time
import pandas as pd
import numpy as np
import astropy.io.fits as fits
import astropy.time
import sqlite3
import desc.twinkles

def create_ccdVisit_table(data_repo):
    "Create the CcdVisit table."
    registry_file = desc.twinkles.find_registry(data_repo)
    registry = sqlite3.connect(registry_file)
    query = """select taiObs, visit, filter, raft, ccd,
            expTime from raw where channel='0,0' order by visit asc"""
    rows = []
    for row in registry.execute(query):
        taiObs, visit, filter_, raft, ccd, expTime = tuple(row)
        mjd = astropy.time.Time(taiObs[:len('2016-03-18 00:00:00.000000')]).mjd
        rows.append((visit, visit, ccd, raft, filter_, mjd))
    columns = 'ccdVisitId visitId ccdName raftName filterName obsStart'.split()
    return pd.DataFrame(data=rows, columns=columns)

def create_object_table(ref_catalog):
    "Create the Object table."
    data = fits.open(ref_catalog)[1].data

    # Compute number of children per object.
    numChildren = OrderedDict([(objectId, 0) for objectId in data['id']])
    for parentId in data['parent'][np.where(data['parent'] != 0)]:
        numChildren[parentId] += 1

    columns = 'objectId parentObjectId numChildren psRa psDecl'.split()
    dataset = list(zip(data['id'], data['parent'], numChildren.values(),
                       data['coord_ra']*180./np.pi,
                       data['coord_dec']*180./np.pi))
    return pd.DataFrame(data=dataset, columns=columns)

def create_forced_source_table(data_repo, imin=0, imax=1000):
    "Create the ForcedSource table."
    visits = desc.twinkles.get_visits(data_repo)
    columns = 'objectId ccdVisitId psFlux psFlux_Sigma'.split()
    forced = pd.DataFrame([], columns=columns)
    num_visits = 0
    for band, visit_list in visits.iteritems():
        for ccdVisitId in visit_list:
            num_visits += 1
            if num_visits < imin+1 or num_visits >= imax+1:
                continue
            visit_name = 'v%i-f%s' % (ccdVisitId, band)
            catalog = os.path.join(data_repo, 'forced', '0',
                                   visit_name, 'R22', 'S11.fits')
            print "Processing", visit_name
            data = fits.open(catalog)[1].data
            flux = data['base_PsfFlux_flux']
            fluxerr = data['base_PsfFlux_fluxSigma']
            # Omit nans:
            index = np.where((flux==flux) & (fluxerr==fluxerr))
            nrows = len(index[0])
            dataset = list(zip(data['objectId'][index], nrows*[ccdVisitId],
                               flux[index], fluxerr[index]))
            forced = forced.append(pd.DataFrame(data=dataset, columns=columns))
    return forced

if __name__ == '__main__':
    data_repo = '/nfs/farm/g/lsst/u1/users/tonyj/Twinkles/run1/985visits'
    ref_catalog = os.path.join(data_repo,
                               'deepCoadd-results/merged/0/0,0/ref-0-0,0.fits')
    ccdVisit = create_ccdVisit_table(data_repo)
    ccdVisit.to_pickle('ccdVisit.pkl')
    object_table = create_object_table(ref_catalog)
    object_table.to_pickle('object_table.pkl')

    indexes = range(0, 985, 50)
    indexes.append(985)
    for imin, imax in zip(indexes[:-1], indexes[1:]):
        print imin, imax
        sys.stdout.flush()
        tstart = time.time()
        forced = create_forced_source_table(data_repo, imin=imin, imax=imax)
        print "execution time:", time.time() - tstart
        forced.to_pickle('forced_%(imin)03i_%(imax)03i.pkl' % locals())
