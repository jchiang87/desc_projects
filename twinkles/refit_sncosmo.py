import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sncosmo
from light_curve_service import LightCurveFactory
plt.ion()

imin, imax = (int(x) for x in sys.argv[1:3])
db_info = dict(database='jc_desc',
               host='ki-sr01.slac.stanford.edu',
               port=3307)

lc_factory = LightCurveFactory(**db_info)

results = pd.read_pickle('sncosmo_results_model_comparisons.pkl')
outfile = 'refit_results_%(imin)04i_%(imax)04i.pkl' % locals()

dust = sncosmo.O94Dust()
model = sncosmo.Model(source=source,
                      effects=[dust, dust],
                      effect_names=['host', 'mw'],
                      effect_frames=['rest', 'obs'])
                      
dustmap = sncosmo.SFD98Map()
ebv = dustmap.get_ebv(ra, dec) # in degrees from truth/DM evaluation of ra, dec
model.set(mwebv=ebv)

dt = 30
for irow in range(imin, imax):
    print irow
    sys.stdout.flush()
    row = results.iloc[irow]
    objectId = int(row.objectId)
    lc = lc_factory.create(objectId)
    # t0.row may be previous iterations but could also be truth values
    # if thse were fixed, we should not add them to the fit_lc call
    model.set(t0=row.t0, z=row.z)
    date_mask = np.where((row.t0 - model.mintime() < lc.data['mjd']) &
                         (lc.data['mjd'] < model.maxtime()) &
                         (lc.data['bandpass'] != 'lsstu'))
    data = lc.data[date_mask]
    try:
        res, fitted_model = sncosmo.fit_lc(data, model,
                                           ['z', 't0', 'x0', 'x1', 'c'],
                                           bounds=dict(z=(0.1, 0.4)))

        for par, value in zip(res['param_names'], res['parameters']):
            results[par].set_value(irow, value)
        results['chisq'].set_value(irow, res.chisq)
        results['ndof'].set_value(irow, res.ndof)
#        sncosmo.plot_lc(data=data, model=fitted_model, errors=res.errors)
    except Exception:
        continue
    results.iloc[imin:imax].to_pickle(outfile)
