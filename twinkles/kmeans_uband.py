import time
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from desc.twinkles.db_table_access import LsstDatabaseTable
from desc.twinkles.lightCurveFactory import LightCurveFactory

def normed_hist(x, bins=20):
    xnorm = x/max(x)
    my_hist = np.histogram(xnorm, bins=bins)
    return my_hist[0]

db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')

jc_desc = LsstDatabaseTable(**db_info)
lc_factory = LightCurveFactory(**db_info)

# Find all of the light curves from deblended sources with chisq > 1e4
query = '''select cs.objectId from Chisq cs join Object obj
           on cs.objectId=obj.objectId
           where cs.dof=252 and cs.chisq>1e4 and obj.numChildren=0'''
object_ids = np.array(jc_desc.apply(query, lambda curs : [x[0] for x in curs]))
print "Found", len(object_ids), 'objects.'

# Get one light curve from the factory to do the mjd conversion.
lc = lc_factory.create(object_ids[0])
lsstu = np.where(lc.data['bandpass'] == 'lsstu')
mjd = lc.data[lsstu]['mjd']

query_tpl = """select fs.psFlux, fs.ccdVisitId
            from ForcedSource fs join CcdVisit cv
            on fs.ccdVisitId=cv.ccdVisitId
            where fs.objectId=%(objectId)i and cv.filterName='%(band)s'
            order by fs.ccdVisitId asc"""

# Fill the data vector with the u band flux values
band = 'u'
X = []
Xhist = []
for objectId in object_ids:
    X.append(jc_desc.apply(query_tpl % locals(),
                           lambda curs : np.array([x[0] for x in curs])))
    Xhist.append(normed_hist(X[-1]))
X = np.array(X)

n_clusters = 5
n_init = 10
k_means = KMeans(init='k-means++', n_clusters=n_clusters, n_init=n_init)
t0 = time.time()
k_means.fit(Xhist)
print 'elapsed time:', time.time() - t0
labels = k_means.labels_
centers = k_means.cluster_centers_

plt.ion()
plt.rcParams['figure.figsize'] = (20, 5)
for label, center in enumerate(centers):
    index = np.where(labels == label)
    fig = plt.figure()
    fig.add_subplot(141).set_title('histograms center')
    plt.scatter(range(20), center)
    fig.add_subplot(142).set_title('objectId: %i' % object_ids[index][0])
    plt.scatter(mjd, X[index][0])
    fig.add_subplot(143).set_title('objectId: %i' % object_ids[index][1])
    plt.scatter(mjd, X[index][1])
    fig.add_subplot(144).set_title('objectId: %i' % object_ids[index][2])
    plt.scatter(mjd, X[index][2])

def plot_sampler(label, nsamp=5):
    ids = object_ids[np.where(labels==label)]
    for id in ids[:nsamp]:
        print id
        lc = lc_factory.create(id)
        lc.plot()
