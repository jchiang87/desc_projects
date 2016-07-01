from __future__ import print_function, absolute_import, division
import numpy as np
import matplotlib.pyplot as plt
import lsst.afw.math as afwMath
import desc.monitor

__all__ = ['find_peaks']

plt.ion()

def find_peaks(flux, nsig=5, min_peak_flux=1):
    stats = afwMath.makeStatistics(flux, afwMath.MEDIAN | afwMath.STDEVCLIP)

    median = stats.getValue(afwMath.MEDIAN)
    stdev = stats.getValue(afwMath.STDEVCLIP)
    threshold = median + nsig*stdev

    index = np.where(flux > threshold)
    dindex = index[0][1:] - index[0][:-1]
    starts = [index[0][0]]
    stops = []
    for i, item in enumerate(dindex):
        if item != 1:
            stops.append(index[0][i])
            starts.append(index[0][i+1])
    stops.append(index[0][-1])

    peaks = []
    for start, stop in zip(starts, stops):
        max_flux = None
        for i in range(start, stop+1):
            if flux[i] > max_flux or max_flux is None:
                max_flux = flux[i]
                ipeak = i
        if flux[ipeak] > min_peak_flux:
            peaks.append(ipeak)
    return (peaks,), threshold, min_peak_flux

if __name__ == '__main__':
    repo = '/nfs/farm/g/desc/u1/users/jchiang/desc_projects/twinkles/Run1.1/output'

    db_info = dict(host='ki-sr01.slac.stanford.edu',
                   port='3307',
                   database='jc_desc')

    l2_service = desc.monitor.Level2DataService(repo, db_info=db_info)

#    objectId = 50302
#    band = 'u'
    objectId = 1026
#    objectId = 4483
    band = 'r'

    lc = l2_service.get_light_curve(objectId, band)

    plt.errorbar(lc['mjd'], lc['flux'], yerr=lc['fluxerr'], fmt='.',
                 color='blue')
    plt.xlabel('MJD')
    plt.ylabel('%(band)s band flux (nmgy)' % locals())

    peaks, threshold, min_peak_flux = find_peaks(lc['flux'])

    xaxis_range = plt.axis()[:2]
    plt.plot(xaxis_range, (threshold, threshold), 'k:')
    plt.plot(xaxis_range, (min_peak_flux, min_peak_flux), 'k--')
    plt.errorbar(lc['mjd'][peaks], lc['flux'][peaks], color='red', fmt='.')
