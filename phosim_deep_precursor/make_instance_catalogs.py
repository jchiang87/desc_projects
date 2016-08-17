import os
from lsst.sims.catalogs.generation.db import CatalogDBObject
from lsst.sims.catalogs.measures.instance import CompoundInstanceCatalog
from lsst.sims.catUtils.baseCatalogModels import BaseCatalogConfig
from lsst.sims.catUtils.baseCatalogModels import GalaxyTileCompoundObj
from lsst.sims.catUtils.utils import ObservationMetaDataGenerator
from lsst.sims.catUtils.exampleCatalogDefinitions.phoSimCatalogExamples import \
        PhoSimCatalogPoint, PhoSimCatalogSersic2D, PhoSimCatalogZPoint

# OpSim db file used for Twinkles Run1.1.
opsim_db = 'kraken_1042_sqlite.db'

# The Twinkles field.
fieldID = 1427
boundLength = 2.5  # radius of extraction region in degrees
#boundLength = 0.3  # radius of extraction region in degrees

config = dict(database='LSSTCATSIM',
              port=1433,
              host='fatboy.phys.washington.edu',
              driver='mssql+pymssql')

gen = ObservationMetaDataGenerator(database=opsim_db, driver='sqlite')
star_objs = ['msstars', 'bhbstars', 'wdstars', 'rrlystars', 'cepheidstars']
gal_objs = ['galaxyBulge', 'galaxyDisk']

# Selected r-band visits from Twinkles Run 1.1
obsHistIDs = (1668469, 1648025, 1414156, 1973403, 921297)
band = 'r'
for obsHistID in obsHistIDs[2:]:
    outfile = 'phosim_input_%s_%07i_%.1fdeg.txt' % (band, obsHistID,
                                                    boundLength)
    outfile = os.path.join('/nfs/farm/g/desc/u1/data/PhoSim-Deep-Precursor',
                           outfile)
    obs_md = gen.getObservationMetaData(obsHistID=obsHistID,
                                        boundLength=boundLength)[0]
    do_header = True
    for objid in star_objs:
        print "processing", objid
        try:
            db_obj = CatalogDBObject.from_objid(objid, **config)
            phosim_object = PhoSimCatalogPoint(db_obj, obs_metadata=obs_md)
            if do_header:
                with open(outfile, 'w') as file_obj:
                    phosim_object.write_header(file_obj)
                do_header = False
            phosim_object.write_catalog(outfile, write_mode='a',
                                        write_header=False, chunk_size=20000)
        except Exception as eObj:
            print type(eObj)
            print eObj.message

    for objid in gal_objs:
        print "processing", objid
        try:
            db_obj = CatalogDBObject.from_objid(objid, **config)
            phosim_object = PhoSimCatalogSersic2D(db_obj, obs_metadata=obs_md)
            phosim_object.write_catalog(outfile, write_mode='a',
                                        write_header=False, chunk_size=20000)
        except Exception as eObj:
            print type(eObj)
            print eObj.message
