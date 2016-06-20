from __future__ import print_function, division
import os
import pandas as pd
import pymssql
import matplotlib.pyplot as plt
import lsst.daf.persistence as dafPersist
import lsst.sims.catUtils.baseCatalogModels as bcm
from lsst.sims.photUtils import BandpassDict
import lsst.utils
from desc.monitor import RefLightCurves
plt.ion()

class RefLightCurveServer(object):
    def __init__(self, idSequence, opsim_csv=None, db_config=None):
        if opsim_csv is None:
            opsim_csv = os.path.join(lsst.utils.getPackageDir('monitor'),
                                     'data', 'SelectedKrakenVisits.csv')
        df = pd.read_csv(opsim_csv, index_col='obsHistID')
        opsim_df = df[['expMJD', 'filter', 'fiveSigmaDepth']]

        lsstBP = BandpassDict.loadBandpassesFromFiles()[0]
        self.reflc = RefLightCurves(idSequence=idSequence,
                                    tableName='TwinkSN',
                                    bandPassDict=lsstBP,
                                    observations=opsim_df)

    def lightCurve(self, idValue, band):
        return self.reflc.lightCurve(idValue, bandName=band)

if __name__ == '__main__':
    idSequence = (6144007055260714, 6145673903924266)
    ref_lc_server = RefLightCurveServer(idSequence)

    band = 'r'
    for idValue in idSequence:
        lc = ref_lc_server.lightCurve(idValue, band)

        fig = plt.figure()
        plt.errorbar(lc['time'], lc['flux'], yerr=lc['fluxerr'].tolist(),
                     fmt='o')
        plt.xlabel('MJD')
        plt.ylabel('%(band)s band flux' % locals())
        plt.annotate('sourceID: %s' % idValue, (0.05, 0.9),
                     xycoords='axes fraction', size='small')

        foo = ref_lc_server.reflc.get_params(idValue)
        print(foo)
