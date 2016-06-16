# find mean (u band) fluxes for each object
# select sources brighter than some mean flux limit
# Do spatial correlation with Level 2 objects
#    * initial query within a small window (<10x10 square arcsec)
#    * associate based on flux and distance
from __future__ import print_function
import numpy as np
import astropy.time
import pandas as pd
import matplotlib.pyplot as plt
import desc.pserv
plt.ion()

class GetData(object):
    def __init__(self, columns):
        self.columns = columns
    def __call__(self, curs):
        return pd.DataFrame(data=[x for x in curs], columns=self.columns)

connect = desc.pserv.DbConnection(db='jc_desc',
                                  read_default_file='~/.my.cnf')

query = """select po.sourceId, po.Ra, po.Decl, lcstats.radius
           from PhosimObject po join
           PhosimLightCurveStats lcstats on po.sourceId=lcstats.sourceId
           where lcstats.dof=249 and lcstats.chisq>1e3 and
           lcstats.radius<1950 order by lcstats.chisq desc limit 30"""
objs = connect.apply(query, GetData('sourceId RA Dec radius'.split()))

band = 'u'
for sourceId, radius in zip(objs['sourceId'].tolist(),
                            objs['radius'].tolist()):
    print(sourceId, radius)
    query = """select cv.obsStart, pcc.numPhotons from
               PhosimCentroidCounts pcc join CcdVisit cv
               on pcc.ccdVisitId=cv.ccdVisitId where
               sourceId=%(sourceId)s and cv.filterName='%(band)s'""" % locals()
    data = connect.apply(query, GetData('obsStart numPhot'.split()))
    mjd = astropy.time.Time(np.array(data['obsStart'].tolist())).mjd
    fig = plt.figure()
    plt.errorbar(mjd, data['numPhot'], yerr=np.sqrt(data['numPhot']), fmt='o')
    plt.xlabel('mjd')
    plt.ylabel('numPhotons')
    plt.title(str(sourceId))
