import sys
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sncosmo
from light_curve_service import LightCurveFactory
plt.ion()

db_info = dict(database='jc_desc',
               host='ki-sr01.slac.stanford.edu',
               port=3307)

lc_factory = LightCurveFactory(**db_info)

infiles = sorted(glob.glob('refit_results_[0-9]*.pkl'))
print infiles
results = pd.concat([pd.read_pickle(infile) for infile in infiles])

selection = (results['z'] > 0.39)
#plt.hist(results[selection]['z'], histtype='step', bins=50)

subset = results[selection]
print len(subset)

dt = 30
for loc in subset.index:
    print loc
    row = subset.loc[loc]
    print row
    objectId = int(row.objectId)
    lc = lc_factory.create(objectId)
    date_mask = np.where((row.t0 - 30 < lc.data['mjd']) &
                         (lc.data['mjd'] < row.t0 + 30) &
                         (lc.data['bandpass'] != 'lsstu'))
    data = lc.data[date_mask]
    model = sncosmo.Model(source='salt2-extended')
    model.set(t0=row.t0, z=row.z)
    try:
        res, fitted_model = sncosmo.fit_lc(data, model,
                                           ['z', 't0', 'x0', 'x1', 'c'],
                                           bounds=dict(z=(0, 1.)))

        for par, value in zip(res['param_names'], res['parameters']):
            results[par].set_value(loc, value)
        results['chisq'].set_value(loc, res.chisq)
        results['ndof'].set_value(loc, res.ndof)
#        sncosmo.plot_lc(data=data, model=fitted_model, errors=res.errors)
    except Exception:
        continue
    sys.stdout.flush()

    results.to_pickle('refit_results_round_2.pkl')
