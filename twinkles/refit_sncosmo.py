import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sncosmo
import desc.monitor
plt.ion()

imin, imax = (int(x) for x in sys.argv[1:3])
db_info = dict(database='jc_desc',
               host='ki-sr01.slac.stanford.edu',
               port=3307)

results = pd.read_pickle('refit_results_round_3.pkl')
outfile = 'refit_results_%(imin)04i_%(imax)04i.pkl' % locals()

dust = sncosmo.OD94Dust()
model = sncosmo.Model(source='salt2-extended',
                      effects=[dust, dust],
                      effect_names=['host', 'mw'],
                      effect_frames=['rest', 'obs'])

for irow in range(imin, imax):
    print irow
    sys.stdout.flush()
    row = results.iloc[irow]
    objectId = int(row.objectId)
    lc = desc.monitor.LightCurve()
    lc.build_lightcurve_from_db(objectId, **db_info)
    # t0.row may be previous iterations but could also be truth values
    # if thse were fixed, we should not add them to the fit_lc call
    model.set(t0=row.t0, z=row.z)
    dustmap = sncosmo.SFD98Map()
    # ra, dec in degrees from truth/DM evaluation of ra, dec
    ebv = dustmap.get_ebv((row.ra, row.dec))
    model.set(mwebv=ebv)
    date_mask = np.where((model.mintime() < lc.lightcurve['mjd']) &
                         (lc.lightcurve['mjd'] < model.maxtime()) &
                         (lc.lightcurve['bandpass'] != 'lsstu'))
    data = lc.lightcurve[date_mask]
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
