import sys
import numpy as np
from scipy.special import gammaincc
from desc.twinkles.db_table_access import LsstDatabaseTable
from desc.twinkles.lightCurveFactory import LightCurveFactory

class ChisqTable(LsstDatabaseTable):
    def __init__(self, **db_info):
        self._table_name = 'Chisq'
        super(ChisqTable, self).__init__(**db_info)

    def _create_table(self):
        query = """create table Chisq (objectId BIGINT,
                   filterName CHAR(1),
                   chisq FLOAT,
                   dof INT,
                   chi2prob FLOAT,
                   primary key (objectId, filterName))"""
        self.apply(query)

    def insert_row(self, objectId, band, chisq, dof):
        chi2prob = gammaincc(dof/2., chisq/2.)
        query = """insert into Chisq set objectId=%(objectId)i,
                   filterName='%(band)s', chisq=%(chisq)12.4e,
                   dof=%(dof)i, chi2prob=%(chi2prob)12.4e
                   on duplicate key update
                   chisq=%(chisq)12.4e, dof=%(dof)i,
                   chi2prob=%(chi2prob)12.4e""" % locals()
        self.apply(query)

db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')
lc_factory = LightCurveFactory(**db_info)
chisq_table = ChisqTable(**db_info)

object_ids = lc_factory.getObjectIds()

nobjs = len(object_ids)
nproc = 1
band = 'u'
for objectId in object_ids:
    lc = lc_factory.create(objectId)
    if nproc % (nobjs/100) == 0:
        if nproc % (nobjs/20) == 0:
            sys.stdout.write('!')
        else:
            sys.stdout.write('.')
        sys.stdout.flush()
    my_band = np.where((lc.data.columns['bandpass'] == ('lsst%s' % band)) &
                       (lc.data.columns['fluxerr'] != 0))
    x, y, yerr = lc.data[my_band]['mjd'], lc.data[my_band]['flux'], \
        lc.data[my_band]['fluxerr']
    nproc += 1
    if len(x) < 20:
        continue
    result = np.polyfit(x, y, 0, w=1./yerr**2)
    func = np.poly1d(result)
    chisq = sum((func(x) - y)**2/yerr**2)
    dof = len(x) - 1
    chisq_table.insert_row(objectId, band, chisq, dof)
