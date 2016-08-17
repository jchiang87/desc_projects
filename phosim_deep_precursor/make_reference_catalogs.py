#!/usr/bin/env python
from __future__ import absolute_import
import numpy
from lsst.sims.catalogs.generation.db import CatalogDBObject
from lsst.sims.catalogs.measures.instance import InstanceCatalog
from lsst.sims.catUtils.mixins import AstrometryStars, PhotometryStars
from lsst.sims.catUtils.utils import ObservationMetaDataGenerator

class TwinklesReference(InstanceCatalog, AstrometryStars, PhotometryStars):
    catalog_type = 'twinkles_ref_star'
    column_outputs = ['uniqueId', 'raJ2000', 'decJ2000', 'lsst_g',
                      'lsst_r', 'lsst_i', 'starnotgal',
                      'isvariable']
    default_columns = [('isresolved', 0, int), ('isvariable', 0, int)]
    default_formats = {'S': '%s', 'f': '%.8f', 'i': '%i'}
    transformations = {'raJ2000': numpy.degrees, 'decJ2000': numpy.degrees}

config = dict(database='LSSTCATSIM',
              port=1433,
              host='fatboy.phys.washington.edu',
              driver='mssql+pymssql')

opsim_db = 'kraken_1042_sqlite.db'
gen = ObservationMetaDataGenerator(database=opsim_db, driver='sqlite')
boundLength = 2.5

obsHistIDs = (921297, 1668469)
for obsHistID in obsHistIDs:
    obs_metadata = gen.getObservationMetaData(obsHistID=obsHistID,
                                              boundLength=boundLength)[0]
    stars = CatalogDBObject.from_objid('allstars', **config)
    while True:
        try:
            ref_stars = TwinklesReference(stars, obs_metadata=obs_metadata)
            break
        except RuntimeError:
            continue
    outfile = 'ref_cat_%i.txt' % obsHistID
    ref_stars.write_catalog(outfile, write_mode='w', write_header=True,
                            chunk_size=20000)
