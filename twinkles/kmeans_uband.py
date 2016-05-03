import time
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from desc.pserv import DbConnection
from light_curve_service import LightCurveFactory
plt.ion()

def normed_hist(x, bins=20):
    xnorm = x/max(x)
    my_hist = np.histogram(xnorm, bins=bins)
    return my_hist[0]

db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')

jc_desc = DbConnection(**db_info)
lc_factory = LightCurveFactory(**db_info)

band = 'u'
#band = 'r'

# find the number of visits for the selected band
num_visits = jc_desc.apply("select count(1) from CcdVisit where filterName='%(band)s'" % locals(), lambda curs: [x[0] for x in curs][0])
dof = num_visits - 1

# Find all of the light curves from deblended sources with chisq > 1e4
query = '''select cs.objectId from Chisq cs
           join Object obj on cs.objectId=obj.objectId
           join ObjectNumChildren numCh on obj.objectId=numCh.objectId
           where cs.filterName='%(band)s' and cs.dof=%(dof)i
           and cs.chisq > 1e4
           and numCh.numChildren=0''' % locals()
object_ids = np.array(jc_desc.apply(query, lambda curs : [x[0] for x in curs]))
print query
print 'Found', len(object_ids), 'deblended variable objects for K-means analysis.'

# Get one light curve from the factory to do the mjd conversion.
lc = lc_factory.create(object_ids[0])
lsstu = np.where(lc.data['bandpass'] == 'lsst%(band)s' % locals())
mjd = lc.data[lsstu]['mjd']

query_tpl = """select fs.psFlux, fs.ccdVisitId
            from ForcedSource fs join CcdVisit cv
            on fs.ccdVisitId=cv.ccdVisitId
            where fs.objectId=%(objectId)i and cv.filterName='%(band)s'
            and fs.psFlux_Sigma!=0
            order by fs.ccdVisitId asc"""

# Fill the data vector with the band flux values
X = []
Xhist = []
for objectId in object_ids:
    X.append(jc_desc.apply(query_tpl % locals(),
                           lambda curs : np.array([x[0] for x in curs])))
    Xhist.append(normed_hist(X[-1]))
X = np.array(X)
Xhist = np.array(Xhist)

n_clusters = 5
n_init = 10
k_means = KMeans(init='k-means++', n_clusters=n_clusters, n_init=n_init)
t0 = time.time()
k_means.fit(Xhist)
#print 'elapsed time:', time.time() - t0
labels = k_means.labels_
centers = k_means.cluster_centers_

plt.rcParams['figure.figsize'] = (20, 5)
for label, center in enumerate(centers):
    index = np.where(labels == label)

    # Plot the histogram cluster and center
    fig = plt.figure()
    fig.add_subplot(141).set_title('histograms')
    for my_xhist in Xhist[index]:
        plt.scatter(range(20), my_xhist, alpha=0.2)
    plt.scatter(range(20), center, color='cyan')

    # Plot the first three light curves in this cluster.
    for i in range(min(3, len(index[0]))):
        fig.add_subplot(142+i).set_title('objectId: %i' % object_ids[index][i])
        plt.scatter(mjd, X[index][i])

def plot_sampler(label, nsamp=5):
    ids = object_ids[np.where(labels==label)]
    for id in ids[:nsamp]:
        print id
        lc = lc_factory.create(id)
        lc.plot()
