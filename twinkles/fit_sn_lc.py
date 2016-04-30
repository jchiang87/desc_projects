import numpy as np
import matplotlib.pyplot as plt
import sncosmo
from desc.twinkles.lightCurveFactory import LightCurveFactory
plt.ion()

db_info = dict(db='jc_fermi', read_default_file='~/.my.cnf')

lc_factory = LightCurveFactory(**db_info)

#objectId = 57576
#mjd_range = (60560, 60595)
#t0 = 60578.

objectId = 4392
mjd_range = (60960, 60988)
t0 = 60970.

lc = lc_factory.create(objectId)

date_mask = np.where((mjd_range[0] < lc.data['mjd'])
                      & (lc.data['mjd'] < mjd_range[1]))

sn1_all = lc.data[date_mask]
sncosmo.plot_lc(sn1_all)

band_mask = np.where((mjd_range[0] < lc.data['mjd'])
                     & (lc.data['mjd'] < mjd_range[1])
#                     & (lc.data['bandpass'] != 'lsstu')
#                     & (lc.data['bandpass'] != 'lsstg')
#                     & (lc.data['bandpass'] != 'lsstr')
#                     & (lc.data['bandpass'] != 'lssti')
#                     & (lc.data['bandpass'] != 'lsstz')
#                     & (lc.data['bandpass'] != 'lssty')
                     )
sn1 = lc.data[band_mask]

model = sncosmo.Model(source='salt2-extended')
model.set(t0=t0)
res, fitted_model = sncosmo.fit_lc(sn1, model,
                                   ['z', 't0', 'x0', 'x1', 'c'],
                                   bounds=dict(z=(0.01, 2.)))

sncosmo.plot_lc(data=sn1, model=fitted_model, errors=res.errors)
