import os
import numpy as np
import unittest
import sncosmo
from desc.twinkles.lightCurveFactory import LightCurveFactory

class LightCurveFactoryTestCase(unittest.TestCase):
    """
    Tests for Twinkles LightCurveFactory.
    """
    def setUp(self):
        db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')
        self.lc_factory = LightCurveFactory(**db_info)

    def tearDown(self):
        del self.lc_factory

    def test_lsst_bandpass_range(self):
        """
        Test the wavelength range of the LSST bandpasses registered
        with sncosmo.
        """
        for band in 'ugrizy':
            # Get throughputs from the Stack.
            bp_file = os.path.join(os.environ['THROUGHPUTS_DIR'], 'baseline',
                                   'total_%s.dat' % band)
            bp_data = np.genfromtxt(bp_file, names=['wavelen', 'transmission'])
            # Compare wavelength range to sncosmo data.
            bandpass = sncosmo.get_bandpass('lsst%s' % band)
            # Convert to Angstroms
            wls = bp_data['wavelen']*10.
            self.assertAlmostEqual(wls[0], bandpass.wave[0])
            self.assertAlmostEqual(wls[-1], bandpass.wave[-1])

if __name__ == '__main__':
    unittest.main()
