"""
Example unit tests for lsst_galsim package
"""
import unittest
import desc.lsst_galsim

class lsst_galsimTestCase(unittest.TestCase):
    def setUp(self):
        self.message = 'Hello, world'
        
    def tearDown(self):
        pass

    def test_run(self):
        foo = desc.lsst_galsim.lsst_galsim(self.message)
        self.assertEquals(foo.run(), self.message)

    def test_failure(self):
        self.assertRaises(TypeError, desc.lsst_galsim.lsst_galsim)
        foo = desc.lsst_galsim.lsst_galsim(self.message)
        self.assertRaises(RuntimeError, foo.run, True)

if __name__ == '__main__':
    unittest.main()
