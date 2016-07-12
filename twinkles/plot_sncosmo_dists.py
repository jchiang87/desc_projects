import glob
from collections import OrderedDict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.ion()

def vline(x_value, marker='k--', label=None):
    return plt.plot((x_value, x_value), plt.axis()[2:], marker, label=label)

results_file = 'refit_results_round_2.pkl'
results = pd.read_pickle(results_file)

#infiles = sorted(glob.glob('refit_results_*.pkl'))
#results = pd.concat([pd.read_pickle(infile) for infile in infiles])
results = results[results['z_model'] > 0]

results['nsig'] = np.sqrt(2.*results['chisq']) - np.sqrt(2.*results['ndof']-1.)
results['dz'] = results['z'] - results['z_model']
results['dt0'] = results['t0'] - results['t0_model']
results['-2.5 log10(x0_model)'] = -2.5*np.log10(results['x0_model'])
results['dlog10x0'] = -2.5*np.log10(results['x0']/results['x0_model'])
results['dx1'] = results['x1'] - results['x1_model']
results['dc'] = results['c'] - results['c_model']

plt.rcParams['figure.figsize'] = 15, 10
fig = plt.figure()

axes = fig.add_subplot(231)
plt.hist(results['nsig'], histtype='step', range=(0, 200), align='mid',
         bins=50, color='k')
plt.xlabel(r'$n_\sigma$')

colors = 'rgb'
selections = []
handles = []
labels = []
#for nsig, color in zip((100, 30, 10), colors):
for nsig, color in zip((10,), colors):
    selections.append(results['nsig'] < nsig)
    handles.extend(vline(nsig, marker=color+'--')),
    labels.append('%i SNe' % len(results[selections[-1]]))
axes.legend(handles, labels)

#dz_range = 0, 0.5
#dz_hist = plt.figure()
#plt.hist(results['dz'], range=dz_range, histtype='step', align='mid',
#         bins=50, color='k')
#plt.xlabel('z - z_model')
#
#for selection, color in zip(selections, colors):
#    plt.hist(results[selection]['dz'], range=dz_range, color=color, bins=50,
#             histtype='step')

fig.add_subplot(232)
for selection, marker, markersize in zip(selections,
                                         [color+'o' for color in colors],
                                         (8, 4, 2)):
    plt.plot(results[selection]['z_model'], results[selection]['dz'],
             marker, markersize=markersize)
plt.xlabel('z_model')
plt.ylabel('z - z_model')

fig.add_subplot(233)
for selection, marker, markersize in zip(selections,
                                         [color+'o' for color in colors],
                                         (8, 4, 2)):
    plt.plot(results[selection]['t0_model']-59580,
             results[selection]['dt0']/1000.,
             marker, markersize=markersize)
plt.xlabel('t0_model (MJD - 59580)')
plt.ylabel('(t0 - t0_model)/1000')

fig.add_subplot(234)
for selection, marker, markersize in zip(selections,
                                         [color+'o' for color in colors],
                                         (8, 4, 2)):
    plt.plot(results[selection]['-2.5 log10(x0_model)'],
             results[selection]['dlog10x0'],
             marker, markersize=markersize)
plt.xlabel('-2.5 log10(x0_model)')
plt.ylabel('-2.5 log10(x0/x0_model)')
#axis_range = list(plt.axis())
#axis_range[2:] = -2.1e-3, 1e-4
#plt.axis(axis_range)

fig.add_subplot(235)
for selection, marker, markersize in zip(selections,
                                         [color+'o' for color in colors],
                                         (8, 4, 2)):
    plt.plot(results[selection]['x1_model'], results[selection]['dx1'],
             marker, markersize=markersize)
plt.xlabel('x1_model')
plt.ylabel('x1 - x1_model')
axis_range = list(plt.axis())
axis_range[2:] = -25, 75
plt.axis(axis_range)

fig.add_subplot(236)
for selection, marker, markersize in zip(selections,
                                         [color+'o' for color in colors],
                                         (8, 4, 2)):
    plt.plot(results[selection]['c_model'], results[selection]['dc'],
             marker, markersize=markersize)
plt.xlabel('c_model')
plt.ylabel('c - c_model')
plt.suptitle('\nTwinkles Run1.1 sncosmo fit parameter comparisons',
             size='large')
plt.savefig('run1.1_sncosmo_fit_param_comparisons.png')

plt.rcParams['figure.figsize'] = 8, 8
plt.figure()

def DM(x0, x1, c):
    return -2.5*np.log10(x0) + 0.11*x1 - 3.11*c

results['delta_DM'] = (DM(results['x0'], results['x1'], results['c']) -
                       DM(results['x0_model'], results['x1_model'],
                          results['c_model']))
for selection, marker, markersize in zip(selections,
                                         [color+'o' for color in colors],
                                         (8, 4, 2)):
    plt.plot(results[selection]['z_model'], results[selection]['delta_DM'],
             marker, markersize=markersize)
plt.xlabel('z_model')
plt.ylabel(r'$\delta (-2.5 \log_{10}x_0 + 0.11 x_1 - 3.11 c)$')



