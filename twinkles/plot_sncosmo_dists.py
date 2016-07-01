import glob
import numpy as np
import pandas as pd
import pylab_plotter as plot
plot.pylab.ion()

#results_file = 'sncosmo_results_model_comparisons.pkl'
#results = pd.read_pickle(results_file)

infiles = sorted(glob.glob('refit_results_*.pkl'))
results = pd.concat([pd.read_pickle(infile) for infile in infiles])

results['nsig'] = np.sqrt(2.*results['chisq']) - np.sqrt(2.*results['ndof']-1.)
results['dz'] = results['z'] - results['z_model']

nsig = plot.histogram(results['nsig'], xname='nsig', xrange=(0, 200))
plot.vline(100, color='r')
plot.vline(30, color='g')
plot.vline(10, color='b')

dz_range = 0, 0.5
dz_hist = plot.histogram(results['dz'], xrange=dz_range, xname='z - z_model')

selection = results['nsig'] < 100.
plot.histogram(results[selection]['dz'], xrange=dz_range, oplot=1, color='r')

z_vs_zmod = plot.xyplot(results[selection]['z_model'], results[selection]['z'],
                        xname='z_model', yname='z', color='r')

selection = results['nsig'] < 30.
plot.set_window(dz_hist)
plot.histogram(results[selection]['dz'], xrange=dz_range, oplot=1, color='g')
plot.set_window(z_vs_zmod)
plot.xyplot(results[selection]['z_model'], results[selection]['z'],
            xname='z_model', yname='z', oplot=1, color='g')

selection = results['nsig'] < 10.
plot.set_window(dz_hist)
plot.histogram(results[selection]['dz'], xrange=dz_range, oplot=1, color='b')
plot.set_window(z_vs_zmod)
plot.xyplot(results[selection]['z_model'], results[selection]['z'],
            xname='z_model', yname='z', oplot=1, color='b')

