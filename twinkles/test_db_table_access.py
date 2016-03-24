import unittest
import desc.twinkles.db_table_access as db_table_access

db_available = False
try:
    test = db_table_access.LsstDatabaseTable(db='jc_desc',
                                             read_default_file='~/.my.cnf')
    del test
    db_available = True
except Exception, eobj:
    #print eobj
    pass


@unittest.skipUnless(db_available, "MySQL database not available")
class db_table_access_TestCase(unittest.TestCase):
    "Test db_table_access class."
    def setUp(self):
        "Create set of LsstDatabaseTable objects."
        desc_info = dict(db='jc_desc', read_default_file='~/.my.cnf')
        fermi_info = dict(db='jc_fermi', read_default_file='~/.my.cnf')

        self.jc_desc = db_table_access.LsstDatabaseTable(**desc_info)
        self.forced = db_table_access.ForcedSourceTable(**desc_info)
        self.ccdVisit = db_table_access.CcdVisitTable(**desc_info)
        self.jc_fermi = db_table_access.LsstDatabaseTable(**fermi_info)

    def tearDown(self):
        "Delete the LsstDatabaseTable objects."
        try:
            del self.jc_desc
        except AttributeError:
            pass
        try:
            del self.forced
        except AttributeError:
            pass
        try:
            del self.ccdVisit
        except AttributeError:
            pass
        try:
            del self.jc_fermi
        except AttributeError:
            pass

    def test_table_names(self):
        "Test that the tables have the expected names."
        self.assertEqual(self.jc_desc._table_name, '')
        self.assertEqual(self.forced._table_name, 'ForcedSource')
        self.assertEqual(self.ccdVisit._table_name, 'CcdVisit')
        self.assertEqual(self.jc_fermi._table_name, '')

    def test_connection_pool(self):
        """
        Test that connection objects match for objects with the same
        connection info.
        """
        self.assertEqual(self.jc_desc._mysql_connection,
                         self.forced._mysql_connection)
        self.assertEqual(self.jc_desc._mysql_connection,
                         self.ccdVisit._mysql_connection)
        self.assertNotEqual(self.jc_desc._mysql_connection,
                            self.jc_fermi._mysql_connection)

    def test_connection_ref_counts(self):
        "Test the reference counts."
        key = self.jc_desc._conn_key
        self.assertEqual(self.jc_desc._LsstDatabaseTable__connection_refs[key],
                         3)
        key = self.jc_fermi._conn_key
        self.assertEqual(self.jc_fermi._LsstDatabaseTable__connection_refs[key],
                         1)

    def test_destructor(self):
        "Test the destructor for correct connection management."
        del self.jc_desc
        key = self.forced._conn_key
        self.assertEqual(self.forced._LsstDatabaseTable__connection_refs[key],
                         2)
        del self.forced
        key = self.ccdVisit._conn_key
        self.assertEqual(self.ccdVisit._LsstDatabaseTable__connection_refs[key],
                         1)
        del self.ccdVisit
        self.assertEqual(len(self.jc_fermi._LsstDatabaseTable__connection_refs),
                         1)
        self.assertEqual(len(self.jc_fermi._LsstDatabaseTable__connection_pool),
                         1)

if __name__ == '__main__':
    unittest.main()
