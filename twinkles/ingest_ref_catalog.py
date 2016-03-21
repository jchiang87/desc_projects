import os
import desc.twinkles.db_table_access as db_table_access

db_info = dict(db='jc_desc', read_default_file='~/.my.cnf')

object_table = db_table_access.ObjectTable(**db_info)

ref_catalog = 'output/deepCoadd-results/merged/0/0,0/ref-0-0,0.fits'

object_table.ingestRefCatalog(ref_catalog)
